"""Agent tools for interacting with Show Your App database and browser."""

import re
from pathlib import Path
from typing import Optional

import httpx
from pydantic_ai import RunContext
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import App, Tool, Tag, AppMedia, AppStatus
from app.agent.deps import AgentDeps
from app.agent.browser import get_browser
from app.core.config import settings


def _generate_slug(title: str) -> str:
    """Generate a URL-friendly slug from a title."""
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug[:100]  # Limit length


async def get_available_tools(ctx: RunContext[AgentDeps]) -> list[dict]:
    """Get all available tools (how apps are built) from the database.
    
    Returns a list of tools with their IDs and names. Use these IDs when creating apps.
    """
    if ctx.deps.tools_list:
        return ctx.deps.tools_list
    
    result = await ctx.deps.db.execute(select(Tool).order_by(Tool.id))
    tools = result.scalars().all()
    ctx.deps.tools_list = [{"id": t.id, "name": t.name} for t in tools]
    return ctx.deps.tools_list


async def get_available_tags(ctx: RunContext[AgentDeps]) -> list[dict]:
    """Get all available tags (categories) from the database.
    
    Returns a list of tags with their IDs and names. Use these IDs when creating apps.
    """
    if ctx.deps.tags_list:
        return ctx.deps.tags_list
    
    result = await ctx.deps.db.execute(select(Tag).order_by(Tag.id))
    tags = result.scalars().all()
    ctx.deps.tags_list = [{"id": t.id, "name": t.name} for t in tags]
    return ctx.deps.tags_list


async def get_my_apps(ctx: RunContext[AgentDeps]) -> list[dict]:
    """Get apps created by the current user.
    
    Use this to check for duplicates before creating a new app.
    Returns a list of apps with their IDs, titles, and URLs.
    """
    if ctx.deps.user_apps:
        return ctx.deps.user_apps
    
    result = await ctx.deps.db.execute(
        select(App)
        .filter(App.creator_id == ctx.deps.user.id)
        .order_by(App.created_at.desc())
        .limit(100)
    )
    apps = result.scalars().all()
    ctx.deps.user_apps = [
        {
            "id": a.id,
            "title": a.title,
            "slug": a.slug,
            "status": a.status.value if a.status else None,
            "app_url": a.app_url,
        }
        for a in apps
    ]
    return ctx.deps.user_apps


async def create_app(
    ctx: RunContext[AgentDeps],
    title: str,
    prompt_text: str,
    prd_text: str,
    status: str,
    tool_ids: list[int],
    tag_ids: list[int],
    app_url: Optional[str] = None,
    youtube_url: Optional[str] = None,
) -> dict:
    """Create a new app listing on Show Your App.
    
    Args:
        title: App name (be specific, not generic)
        prompt_text: 1-2 sentence hook that sells the app
        prd_text: Full description in HTML format (use <h2>, <p>, <ul>, <li> tags)
        status: One of "Concept", "WIP", or "Live"
        tool_ids: List of tool IDs (from get_available_tools)
        tag_ids: List of tag IDs (from get_available_tags)
        app_url: URL to the live app (required if status is "Live")
        youtube_url: Optional YouTube demo video URL
        
    Returns:
        Dict with created app ID and slug, or error message.
    """
    # Validate status
    try:
        app_status = AppStatus(status)
    except ValueError:
        return {"error": f"Invalid status: {status}. Must be 'Concept', 'WIP', or 'Live'."}
    
    # Validate app_url for Live status
    if app_status == AppStatus.LIVE and not app_url:
        return {"error": "app_url is required when status is 'Live'"}
    
    # Generate unique slug
    base_slug = _generate_slug(title)
    slug = base_slug
    counter = 1
    
    while True:
        existing = await ctx.deps.db.execute(
            select(App).filter(App.slug == slug)
        )
        if not existing.scalar():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Create app
    app = App(
        creator_id=ctx.deps.user.id,
        title=title,
        prompt_text=prompt_text,
        prd_text=prd_text,
        status=app_status,
        slug=slug,
        app_url=app_url,
        youtube_url=youtube_url,
        is_agent_submitted=True,
        is_owner=True,
    )
    
    # Add tools
    if tool_ids:
        tools_result = await ctx.deps.db.execute(
            select(Tool).filter(Tool.id.in_(tool_ids))
        )
        app.tools = list(tools_result.scalars().all())
    
    # Add tags
    if tag_ids:
        tags_result = await ctx.deps.db.execute(
            select(Tag).filter(Tag.id.in_(tag_ids))
        )
        app.tags = list(tags_result.scalars().all())
    
    ctx.deps.db.add(app)
    await ctx.deps.db.flush()
    
    # Track created app
    ctx.deps.created_app_ids.append(app.id)
    
    return {
        "success": True,
        "app_id": app.id,
        "slug": app.slug,
        "title": app.title,
        "url": f"https://show-your.app/apps/{app.slug}",
    }


async def update_app(
    ctx: RunContext[AgentDeps],
    app_id: int,
    title: Optional[str] = None,
    prompt_text: Optional[str] = None,
    prd_text: Optional[str] = None,
    status: Optional[str] = None,
    tool_ids: Optional[list[int]] = None,
    tag_ids: Optional[list[int]] = None,
    app_url: Optional[str] = None,
    youtube_url: Optional[str] = None,
) -> dict:
    """Update an existing app listing.
    
    Only provide the fields you want to change.
    
    Args:
        app_id: ID of the app to update
        title: New app name
        prompt_text: New hook text
        prd_text: New description (HTML format)
        status: New status ("Concept", "WIP", or "Live")
        tool_ids: New list of tool IDs
        tag_ids: New list of tag IDs
        app_url: New app URL
        youtube_url: New YouTube URL
        
    Returns:
        Dict with success status or error message.
    """
    # Get the app
    result = await ctx.deps.db.execute(
        select(App)
        .options(selectinload(App.tools), selectinload(App.tags))
        .filter(App.id == app_id, App.creator_id == ctx.deps.user.id)
    )
    app = result.scalar()
    
    if not app:
        return {"error": f"App with ID {app_id} not found or you don't have permission to edit it."}
    
    # Update fields
    if title is not None:
        app.title = title
        # Update slug too
        base_slug = _generate_slug(title)
        slug = base_slug
        counter = 1
        while True:
            existing = await ctx.deps.db.execute(
                select(App).filter(App.slug == slug, App.id != app_id)
            )
            if not existing.scalar():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        app.slug = slug
    
    if prompt_text is not None:
        app.prompt_text = prompt_text
    
    if prd_text is not None:
        app.prd_text = prd_text
    
    if status is not None:
        try:
            app.status = AppStatus(status)
        except ValueError:
            return {"error": f"Invalid status: {status}"}
    
    if app_url is not None:
        app.app_url = app_url
    
    if youtube_url is not None:
        app.youtube_url = youtube_url
    
    if tool_ids is not None:
        tools_result = await ctx.deps.db.execute(
            select(Tool).filter(Tool.id.in_(tool_ids))
        )
        app.tools = list(tools_result.scalars().all())
    
    if tag_ids is not None:
        tags_result = await ctx.deps.db.execute(
            select(Tag).filter(Tag.id.in_(tag_ids))
        )
        app.tags = list(tags_result.scalars().all())
    
    await ctx.deps.db.flush()
    
    return {
        "success": True,
        "app_id": app.id,
        "slug": app.slug,
    }


async def get_presigned_url(
    ctx: RunContext[AgentDeps],
    filename: str,
    content_type: str,
) -> dict:
    """Get a presigned URL for uploading media to S3.
    
    Args:
        filename: Name of the file (e.g., "screenshot1.png")
        content_type: MIME type (e.g., "image/png")
        
    Returns:
        Dict with upload_url, download_url, and file_key.
    """
    import boto3
    from botocore.config import Config
    import uuid
    
    if not settings.S3_BUCKET or not settings.AWS_ACCESS_KEY_ID:
        return {"error": "S3 not configured"}
    
    # Generate unique file key
    ext = Path(filename).suffix or ".png"
    file_key = f"media/{uuid.uuid4()}{ext}"
    
    # Create S3 client
    s3_config = Config(signature_version='s3v4')
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        endpoint_url=settings.S3_ENDPOINT_URL,
        config=s3_config,
    )
    
    # Generate presigned URL for upload
    upload_url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.S3_BUCKET,
            'Key': file_key,
            'ContentType': content_type,
        },
        ExpiresIn=3600,
    )
    
    # Generate download URL
    if settings.S3_ENDPOINT_URL:
        download_url = f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET}/{file_key}"
    else:
        download_url = f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
    
    return {
        "success": True,
        "upload_url": upload_url,
        "download_url": download_url,
        "file_key": file_key,
    }


async def upload_file_to_s3(
    ctx: RunContext[AgentDeps],
    file_path: str,
    upload_url: str,
    content_type: str,
) -> dict:
    """Upload a file to S3 using a presigned URL.
    
    Args:
        file_path: Path to the file on disk (from take_screenshot)
        upload_url: The upload_url from get_presigned_url
        content_type: MIME type (e.g., "image/png")
        
    Returns:
        Dict with success status.
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}
    
    try:
        file_data = path.read_bytes()
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                upload_url,
                content=file_data,
                headers={"Content-Type": content_type},
                timeout=120.0,
            )
            response.raise_for_status()
        
        return {
            "success": True,
            "file_path": file_path,
            "size_bytes": len(file_data),
        }
    except Exception as e:
        return {"error": f"Upload failed: {str(e)}"}


async def attach_media_to_app(
    ctx: RunContext[AgentDeps],
    app_id: int,
    media_url: str,
) -> dict:
    """Attach uploaded media to an app listing.
    
    Args:
        app_id: ID of the app
        media_url: The download_url from get_presigned_url
        
    Returns:
        Dict with success status and media ID.
    """
    # Verify app belongs to user
    result = await ctx.deps.db.execute(
        select(App).filter(App.id == app_id, App.creator_id == ctx.deps.user.id)
    )
    app = result.scalar()
    
    if not app:
        return {"error": f"App with ID {app_id} not found or you don't have permission."}
    
    # Create media record
    media = AppMedia(app_id=app_id, media_url=media_url)
    ctx.deps.db.add(media)
    await ctx.deps.db.flush()
    
    return {
        "success": True,
        "media_id": media.id,
        "app_id": app_id,
    }


# Browser tools

async def browser_navigate(ctx: RunContext[AgentDeps], url: str) -> dict:
    """Navigate to a URL in the browser.
    
    Use this to visit an app and explore it before creating a listing.
    
    Args:
        url: The URL to visit
        
    Returns:
        Dict with page title and success status.
    """
    browser = await get_browser(headless=ctx.deps.headless)
    return await browser.navigate(url)


async def browser_screenshot(ctx: RunContext[AgentDeps], name: str) -> dict:
    """Take a screenshot of the current page.
    
    Args:
        name: Name for the screenshot file (e.g., "main-page", "feature-1")
        
    Returns:
        Dict with file_path (use this with upload_file_to_s3).
    """
    browser = await get_browser(headless=ctx.deps.headless)
    return await browser.take_screenshot(name)


async def browser_get_content(ctx: RunContext[AgentDeps]) -> dict:
    """Get the text content of the current page.
    
    Use this to understand what the app does.
    
    Returns:
        Dict with page title, URL, and text content.
    """
    browser = await get_browser(headless=ctx.deps.headless)
    return await browser.get_page_content()


async def browser_click(ctx: RunContext[AgentDeps], selector: str) -> dict:
    """Click an element on the page.
    
    Args:
        selector: CSS selector (e.g., "button.submit", "#start-btn")
        
    Returns:
        Dict with success status.
    """
    browser = await get_browser(headless=ctx.deps.headless)
    return await browser.click(selector)


async def browser_scroll(ctx: RunContext[AgentDeps], direction: str = "down") -> dict:
    """Scroll the page up or down.
    
    Args:
        direction: "up" or "down"
        
    Returns:
        Dict with success status.
    """
    browser = await get_browser(headless=ctx.deps.headless)
    return await browser.scroll(direction)


# Export all tools for registration
ALL_TOOLS = [
    get_available_tools,
    get_available_tags,
    get_my_apps,
    create_app,
    update_app,
    get_presigned_url,
    upload_file_to_s3,
    attach_media_to_app,
    browser_navigate,
    browser_screenshot,
    browser_get_content,
    browser_click,
    browser_scroll,
]
