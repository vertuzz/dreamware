"""Agent tools for interacting with Show Your App database and browser."""

import re
from pathlib import Path
from typing import Optional

import httpx
from pydantic_ai import RunContext
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.models import App, Tool, Tag, AppMedia, AppStatus
from app.agent.deps import AgentDeps
from app.agent.browser import get_browser
from app.core.config import settings
from app.utils import normalize_url


# Browser step limit
MAX_BROWSER_STEPS = 10


def _generate_slug(title: str) -> str:
    """Generate a URL-friendly slug from a title."""
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug[:100]  # Limit length


def _check_browser_limit(ctx: RunContext[AgentDeps]) -> dict | None:
    """Check if browser step limit reached. Returns error dict if exceeded."""
    if ctx.deps.browser_step_count >= MAX_BROWSER_STEPS:
        return {"error": f"Browser step limit ({MAX_BROWSER_STEPS}) reached. Create the app with information gathered so far."}
    ctx.deps.browser_step_count += 1
    return None


async def get_tags_and_tools(ctx: RunContext[AgentDeps]) -> dict:
    """Get all available tags (categories) and tools (how apps are built) from the database.
    
    Returns a dict with:
    - tags: list of tags with IDs and names for categorizing apps
    - tools: list of tools with IDs and names for specifying how apps are built
    
    Use these IDs when creating apps.
    """
    # Fetch tools if not cached
    if not ctx.deps.tools_list:
        result = await ctx.deps.db.execute(select(Tool).order_by(Tool.id))
        tools = result.scalars().all()
        ctx.deps.tools_list = [{"id": t.id, "name": t.name} for t in tools]
    
    # Fetch tags if not cached
    if not ctx.deps.tags_list:
        result = await ctx.deps.db.execute(select(Tag).order_by(Tag.id))
        tags = result.scalars().all()
        ctx.deps.tags_list = [{"id": t.id, "name": t.name} for t in tags]
    
    return {
        "tags": ctx.deps.tags_list,
        "tools": ctx.deps.tools_list,
    }


async def get_my_apps(ctx: RunContext[AgentDeps]) -> list[dict]:
    """Get apps created by the current user.
    
    Use this to check for duplicates before creating a new app.
    Returns a list of apps with their IDs, titles, and URLs.
    """
    if ctx.deps.user_apps:
        return ctx.deps.user_apps
    
    result = await ctx.deps.db.execute(
        select(App)
        .filter(App.creator_id == ctx.deps.user_id)
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


async def search_apps(
    ctx: RunContext[AgentDeps],
    url: Optional[str] = None,
    title: Optional[str] = None,
) -> list[dict]:
    """Search for existing apps platform-wide to check for duplicates.
    
    Use this BEFORE creating a new app to avoid duplicates.
    Search by URL first (most reliable), then by title as fallback.
    
    Args:
        url: The app URL to search for (normalized matching - handles http/https, www variations)
        title: The app title to search for (fuzzy matching)
        
    Returns:
        List of matching apps with id, title, slug, app_url, status, and creator info.
        Empty list if no matches found.
    """
    if not url and not title:
        return {"error": "Must provide either url or title to search"}
    
    query = select(App).options(selectinload(App.creator))
    
    filters = []
    
    # URL-based search (normalized matching)
    if url:
        normalized_input = normalize_url(url)
        if normalized_input:
            # Match against normalized versions of stored URLs
            filters.append(App.app_url.ilike(f"%{normalized_input}%"))
    
    # Title-based search (fuzzy matching)
    if title:
        filters.append(App.title.ilike(f"%{title}%"))
    
    if filters:
        query = query.filter(or_(*filters))
    
    # Limit results and order by newest first
    query = query.order_by(App.created_at.desc()).limit(20)
    
    result = await ctx.deps.db.execute(query)
    apps = result.scalars().all()
    
    return [
        {
            "id": a.id,
            "title": a.title,
            "slug": a.slug,
            "status": a.status.value if a.status else None,
            "app_url": a.app_url,
            "creator": {
                "id": a.creator.id,
                "username": a.creator.username,
            } if a.creator else None,
            "is_mine": a.creator_id == ctx.deps.user_id,
        }
        for a in apps
    ]


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
    post_url: Optional[str] = None,
) -> dict:
    """Create a new app listing on Show Your App.
    
    Automatically uploads any screenshots taken during browser exploration.
    
    Args:
        title: App name (be specific, not generic)
        prompt_text: 1-2 sentence hook that sells the app
        prd_text: Full description in HTML format (use <h2>, <p>, <ul>, <li> tags)
        status: One of "Concept", "WIP", or "Live"
        tool_ids: List of tool IDs (from get_tags_and_tools)
        tag_ids: List of tag IDs (from get_tags_and_tools)
        app_url: URL to the live app (required if status is "Live")
        youtube_url: Optional YouTube demo video URL
        post_url: Optional source URL (e.g., Reddit post permalink) for tracking
        
    Returns:
        Dict with created app ID, slug, media upload results, or error message.
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
    # Agent-submitted apps are always marked as not owned by the submitter
    # since admin is submitting on behalf of someone else
    app = App(
        creator_id=ctx.deps.user_id,
        title=title,
        prompt_text=prompt_text,
        prd_text=prd_text,
        status=app_status,
        slug=slug,
        app_url=app_url,
        youtube_url=youtube_url,
        post_url=post_url,
        is_agent_submitted=True,
        is_owner=False,
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
    
    # Auto-upload saved screenshots
    media_uploaded = 0
    media_errors = []
    
    for screenshot_path in ctx.deps.saved_screenshots:
        upload_result = await _upload_and_attach_media(ctx, app.id, screenshot_path)
        if upload_result.get("success"):
            media_uploaded += 1
        else:
            media_errors.append(f"{Path(screenshot_path).name}: {upload_result.get('error', 'Unknown error')}")
    
    # Clear screenshots after upload attempt
    ctx.deps.saved_screenshots.clear()
    
    result = {
        "success": True,
        "app_id": app.id,
        "slug": app.slug,
        "title": app.title,
        "url": f"https://show-your.app/apps/{app.slug}",
        "media_uploaded": media_uploaded,
    }
    
    if media_errors:
        result["media_errors"] = media_errors
    
    return result


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
        .filter(App.id == app_id, App.creator_id == ctx.deps.user_id)
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


# Private helper functions for media upload (used internally by create_app)

async def _get_presigned_url(filename: str, content_type: str) -> dict:
    """Get a presigned URL for uploading media to S3 (internal helper)."""
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


async def _upload_file_to_s3(file_path: str, upload_url: str, content_type: str) -> dict:
    """Upload a file to S3 using a presigned URL (internal helper)."""
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


async def _upload_and_attach_media(ctx: RunContext[AgentDeps], app_id: int, file_path: str) -> dict:
    """Upload a file to S3 and attach it to an app (internal helper).
    
    Combines presigned URL generation, S3 upload, and AppMedia record creation.
    """
    path = Path(file_path)
    filename = path.name
    
    # Determine content type from extension
    ext = path.suffix.lower()
    content_type_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    content_type = content_type_map.get(ext, "image/png")
    
    # Get presigned URL
    presigned = await _get_presigned_url(filename, content_type)
    if not presigned.get("success"):
        return presigned
    
    # Upload file
    upload_result = await _upload_file_to_s3(file_path, presigned["upload_url"], content_type)
    if not upload_result.get("success"):
        return upload_result
    
    # Create media record
    media = AppMedia(app_id=app_id, media_url=presigned["download_url"])
    ctx.deps.db.add(media)
    await ctx.deps.db.flush()
    
    return {
        "success": True,
        "media_id": media.id,
        "media_url": presigned["download_url"],
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
    limit_error = _check_browser_limit(ctx)
    if limit_error:
        return limit_error
    
    browser = await get_browser(headless=ctx.deps.headless)
    return await browser.navigate(url)


async def browser_screenshot(ctx: RunContext[AgentDeps], name: str) -> dict:
    """Take a screenshot of the current page.
    
    Screenshots are automatically uploaded when you call create_app.
    
    Args:
        name: Name for the screenshot file (e.g., "main-page", "feature-1")
        
    Returns:
        Dict with file_path (automatically uploaded on create_app).
    """
    limit_error = _check_browser_limit(ctx)
    if limit_error:
        return limit_error
    
    browser = await get_browser(headless=ctx.deps.headless)
    result = await browser.take_screenshot(name)
    
    # Track screenshot for auto-upload in create_app
    if result.get("success") and result.get("file_path"):
        ctx.deps.saved_screenshots.append(result["file_path"])
    
    return result


async def browser_get_content(ctx: RunContext[AgentDeps]) -> dict:
    """Get the text content of the current page.
    
    Use this to understand what the app does.
    
    Returns:
        Dict with page title, URL, and text content.
    """
    limit_error = _check_browser_limit(ctx)
    if limit_error:
        return limit_error
    
    browser = await get_browser(headless=ctx.deps.headless)
    return await browser.get_page_content()


async def browser_click(ctx: RunContext[AgentDeps], selector: str) -> dict:
    """Click an element on the page.
    
    Args:
        selector: CSS selector (e.g., "button.submit", "#start-btn")
        
    Returns:
        Dict with success status.
    """
    limit_error = _check_browser_limit(ctx)
    if limit_error:
        return limit_error
    
    browser = await get_browser(headless=ctx.deps.headless)
    return await browser.click(selector)


async def browser_scroll(ctx: RunContext[AgentDeps], direction: str = "down") -> dict:
    """Scroll the page up or down.
    
    Args:
        direction: "up" or "down"
        
    Returns:
        Dict with success status.
    """
    limit_error = _check_browser_limit(ctx)
    if limit_error:
        return limit_error
    
    browser = await get_browser(headless=ctx.deps.headless)
    return await browser.scroll(direction)


# Export all tools for registration
ALL_TOOLS = [
    get_tags_and_tools,
    get_my_apps,
    search_apps,
    create_app,
    update_app,
    browser_navigate,
    browser_screenshot,
    browser_get_content,
    browser_click,
    browser_scroll,
]
