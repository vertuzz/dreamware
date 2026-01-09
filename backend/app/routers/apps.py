from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, distinct
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.database import get_db, IS_POSTGRES
from app.models import App, User, Tool, Tag, AppMedia, AppStatus, Like, Comment, Review, DeadAppReport, ReportStatus
from app.schemas import schemas
from app.routers.auth import get_current_user, get_current_user_optional, require_admin
from app.utils import slugify, generate_unique_slug, normalize_url
from app.services.telegram import notify_app_created, notify_dead_link_report

router = APIRouter()


async def get_app_counts(db: AsyncSession, app_id: int) -> tuple[int, int]:
    """Get likes and comments counts for a single app."""
    likes_result = await db.execute(
        select(func.count(Like.id)).filter(Like.app_id == app_id)
    )
    comments_result = await db.execute(
        select(func.count(Comment.id)).filter(Comment.app_id == app_id)
    )
    return likes_result.scalar() or 0, comments_result.scalar() or 0


def app_to_schema(
    app: App, 
    creator: Optional[schemas.AppCreator] = None,
    likes_count: int = 0, 
    comments_count: int = 0,
    is_liked: bool = False
) -> schemas.App:
    """Convert App ORM object to dict with computed fields"""
    # Create the schema object directly
    return {
        "id": app.id,
        "title": app.title,
        "prompt_text": app.prompt_text,
        "prd_text": app.prd_text,
        "extra_specs": app.extra_specs,
        "status": app.status,
        "app_url": app.app_url,
        "youtube_url": app.youtube_url,
        "is_agent_submitted": app.is_agent_submitted,
        "is_owner": app.is_owner,
        "is_dead": app.is_dead,
        "creator_id": app.creator_id,
        "parent_app_id": app.parent_app_id,
        "created_at": app.created_at,
        "slug": app.slug,
        "media": app.media,
        "tools": app.tools,
        "tags": app.tags,
        "creator": creator or app.creator,
        "likes_count": likes_count,
        "comments_count": comments_count,
        "is_liked": is_liked,
    }

@router.get("/", response_model=List[schemas.App])
async def get_apps(
    response: Response,
    skip: int = 0,
    limit: int = 20,
    tool_id: Optional[List[int]] = Query(None),
    tag_id: Optional[List[int]] = Query(None),
    tool: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    app_url: Optional[str] = Query(None, description="Filter by app URL (normalized match)"),
    status: Optional[AppStatus] = None,
    creator_id: Optional[int] = None,
    liked_by_user_id: Optional[int] = None,
    include_dead: bool = Query(False, description="Include dead apps in results"),
    sort_by: str = Query("trending", enum=["trending", "newest", "top_rated", "likes"]),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    # Query for the newest app ID (efficient single-row query for polling)
    newest_result = await db.execute(
        select(App.id)
        .filter(App.is_dead == False)
        .order_by(desc(App.created_at), desc(App.id))
        .limit(1)
    )
    newest_app_id = newest_result.scalar()
    if newest_app_id:
        response.headers["X-Newest-App-Id"] = str(newest_app_id)
    
    # Base query with eager loading of media, tools, tags and creator
    query = select(App).options(
        selectinload(App.tools), 
        selectinload(App.tags), 
        selectinload(App.media),
        selectinload(App.creator)
    )
    
    # Filter out dead apps by default
    if not include_dead:
        query = query.filter(App.is_dead == False)
    
    # 1. Joins for filtering and sorting
    if tool_id or tool:
        query = query.join(App.tools)
    if tag_id or tag:
        query = query.join(App.tags)
        
    # 2. Apply Filters
    if tool_id:
        query = query.filter(Tool.id.in_(tool_id))
    elif tool:
        tool_names = [t.strip() for t in tool.split(",") if t.strip()]
        if len(tool_names) > 1:
            query = query.filter(Tool.name.in_(tool_names))
        else:
            query = query.filter(Tool.name.ilike(f"%{tool_names[0]}%"))
        
    if tag_id:
        query = query.filter(Tag.id.in_(tag_id))
    elif tag:
        tag_names = [t.strip() for t in tag.split(",") if t.strip()]
        if len(tag_names) > 1:
            query = query.filter(Tag.name.in_(tag_names))
        else:
            query = query.filter(Tag.name.ilike(f"%{tag_names[0]}%"))
        
    if search:
        query = query.filter(
            (App.title.ilike(f"%{search}%")) |
            (App.prompt_text.ilike(f"%{search}%")) | 
            (App.prd_text.ilike(f"%{search}%")) |
            (App.app_url.ilike(f"%{search}%"))
        )
    
    # Filter by normalized app_url for duplicate detection
    if app_url:
        normalized_input = normalize_url(app_url)
        if normalized_input:
            # Match apps where normalized URL contains our normalized input
            # This handles variations like http vs https, www vs non-www
            query = query.filter(App.app_url.isnot(None))
            # Use ILIKE for case-insensitive partial matching on the URL
            query = query.filter(App.app_url.ilike(f"%{normalized_input}%"))
        
    if status:
        query = query.filter(App.status == status)

    if creator_id:
        query = query.filter(App.creator_id == creator_id)
    
    if liked_by_user_id:
        query = query.filter(App.likes.any(Like.user_id == liked_by_user_id))
    
    # 3. Apply Sorting & Grouping
    # We always group by App.id to avoid duplicates from many-to-many joins
    query = query.group_by(App.id)
    
    if sort_by == "trending":
        # Trending = (Likes + Comments * 2) / (Age + 2)^1.8
        query = query.outerjoin(App.likes).outerjoin(App.comments)
        
        likes_count = func.count(distinct(Like.id))
        comments_count = func.count(distinct(Comment.id))
        
        # Handle SQLite vs Postgres for age calculation (determined at startup)
        if IS_POSTGRES:
            age_in_hours = func.extract('epoch', func.now() - App.created_at) / 3600
        else:
            # SQLite: julianday returns days, so multiply by 24 for hours
            age_in_hours = (func.julianday('now') - func.julianday(App.created_at)) * 24
        
        # Gravity algorithm
        trending_score = (likes_count + (comments_count * 2) + 1) / func.power(age_in_hours + 2, 1.8)
        query = query.order_by(desc(trending_score), desc(App.id))
        
    elif sort_by == "top_rated":
        query = query.outerjoin(App.reviews)
        # Average score, default to 0 if no reviews
        avg_score = func.coalesce(func.avg(Review.score), 0)
        query = query.order_by(desc(avg_score), desc(App.created_at), desc(App.id))
        
    elif sort_by == "likes":
        query = query.outerjoin(App.likes)
        query = query.order_by(desc(func.count(distinct(Like.id))), desc(App.created_at), desc(App.id))
        
    elif sort_by == "newest":
        query = query.order_by(desc(App.created_at), desc(App.id))
    
    else: # Default fallback to created_at
        query = query.order_by(desc(App.created_at), desc(App.id))
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    apps = result.scalars().all()
    
    # Get counts for all apps in a single query
    app_ids = [a.id for a in apps]
    
    if app_ids:
        # Get likes counts
        likes_result = await db.execute(
            select(Like.app_id, func.count(Like.id))
            .filter(Like.app_id.in_(app_ids))
            .group_by(Like.app_id)
        )
        likes_map = dict(likes_result.all())
        
        # Get comments counts
        comments_result = await db.execute(
            select(Comment.app_id, func.count(Comment.id))
            .filter(Comment.app_id.in_(app_ids))
            .group_by(Comment.app_id)
        )
        comments_map = dict(comments_result.all())
    else:
        likes_map = {}
        comments_map = {}
    
    # Get liked status if user is logged in
    liked_app_ids = set()
    if current_user:
        if app_ids:
            likes_q = await db.execute(
                select(Like.app_id)
                .filter(Like.app_id.in_(app_ids))
                .filter(Like.user_id == current_user.id)
            )
            liked_app_ids = set(likes_q.scalars().all())

    # Convert to response with counts
    return [
        app_to_schema(
            app, 
            likes_count=likes_map.get(app.id, 0),
            comments_count=comments_map.get(app.id, 0),
            is_liked=(app.id in liked_app_ids)
        )
        for app in apps
    ]

@router.post("/", response_model=schemas.App)
async def create_app(
    app_in: schemas.AppCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    # Generate slug
    base_slug = slugify(app_in.title)
    slug = base_slug
    
    # Check for uniqueness (simple loop for now, ideally handle with DB constraint exception)
    # Since we are in async, we can do a check.
    # Note: efficient way is to catch IntegrityError but for user feedback check is okay.
    existing = await db.execute(select(App).filter(App.slug == slug))
    if existing.scalar_one_or_none():
        slug = generate_unique_slug(base_slug)

    db_app = App(
        creator_id=current_user.id,
        title=app_in.title,
        prompt_text=app_in.prompt_text,
        prd_text=app_in.prd_text,
        extra_specs=app_in.extra_specs,
        status=app_in.status,
        app_url=app_in.app_url,
        youtube_url=app_in.youtube_url,
        is_agent_submitted=app_in.is_agent_submitted,
        is_owner=app_in.is_owner,
        parent_app_id=app_in.parent_app_id,
        slug=slug
    )
    
    # Add tools and tags
    if app_in.tool_ids:
        result = await db.execute(select(Tool).filter(Tool.id.in_(app_in.tool_ids)))
        tools = result.scalars().all()
        db_app.tools = tools
    if app_in.tag_ids:
        result = await db.execute(select(Tag).filter(Tag.id.in_(app_in.tag_ids)))
        tags = result.scalars().all()
        db_app.tags = tags
        
    db.add(db_app)
    await db.commit()
    # Reload with eager loading
    result = await db.execute(
        select(App)
        .options(selectinload(App.tools), selectinload(App.tags), selectinload(App.media), selectinload(App.creator))
        .filter(App.id == db_app.id)
    )
    app = result.scalars().first()
    return app_to_schema(app, likes_count=0, comments_count=0, is_liked=False)

@router.get("/{app_identifier}", response_model=schemas.App)
async def get_app(
    app_identifier: str, 
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Try to parse as integer ID first
    app_id = None
    if app_identifier.isdigit():
        app_id = int(app_identifier)
        query = select(App).filter(App.id == app_id)
    else:
        query = select(App).filter(App.slug == app_identifier)

    result = await db.execute(
        query.options(selectinload(App.tools), selectinload(App.tags), selectinload(App.media), selectinload(App.creator))
    )
    app = result.scalars().first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    # Get counts
    likes_count, comments_count = await get_app_counts(db, app.id)
    
    # Check if liked
    is_liked = False
    if current_user:
        result_like = await db.execute(
            select(Like).filter(Like.app_id == app.id, Like.user_id == current_user.id)
        )
        if result_like.scalars().first():
            is_liked = True

    return app_to_schema(app, likes_count=likes_count, comments_count=comments_count, is_liked=is_liked)

@router.patch("/{app_id}", response_model=schemas.App)
async def update_app(
    app_id: int,
    app_in: schemas.AppUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(App)
        .options(selectinload(App.tools), selectinload(App.tags), selectinload(App.media), selectinload(App.creator))
        .filter(App.id == app_id)
    )
    db_app = result.scalars().first()
    if not db_app:
        raise HTTPException(status_code=404, detail="App not found")
    if db_app.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = app_in.model_dump(exclude_unset=True)
    
    # Handle tools update
    if "tool_ids" in update_data:
        tool_ids = update_data.pop("tool_ids")
        if tool_ids is not None:
            result = await db.execute(select(Tool).filter(Tool.id.in_(tool_ids)))
            db_app.tools = result.scalars().all()
        else:
            db_app.tools = []
            
    # Handle tags update
    if "tag_ids" in update_data:
        tag_ids = update_data.pop("tag_ids")
        if tag_ids is not None:
            result = await db.execute(select(Tag).filter(Tag.id.in_(tag_ids)))
            db_app.tags = result.scalars().all()
        else:
            db_app.tags = []

    for field, value in update_data.items():
        setattr(db_app, field, value)
    
    db.add(db_app)
    await db.commit()
    # Reload to ensure serialization works
    result = await db.execute(
        select(App)
        .options(selectinload(App.tools), selectinload(App.tags), selectinload(App.media), selectinload(App.creator))
        .filter(App.id == db_app.id)
    )
    app = result.scalars().first()
    
    # Get counts
    likes_count, comments_count = await get_app_counts(db, app_id)
    
    # Check if creator liked their own app
    result_like = await db.execute(
        select(Like).filter(Like.app_id == app.id, Like.user_id == current_user.id)
    )
    is_liked = result_like.scalars().first() is not None
    return app_to_schema(app, likes_count=likes_count, comments_count=comments_count, is_liked=is_liked)

@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(App).filter(App.id == app_id))
    db_app = result.scalars().first()
    
    if not db_app:
        raise HTTPException(status_code=404, detail="App not found")
    if db_app.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Cascade delete is handled by DB relationships usually, but let's be safe or check models
    await db.delete(db_app)
    await db.commit()
    return None

@router.post("/{app_id}/fork", response_model=schemas.App)
async def fork_app(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(App)
        .options(selectinload(App.tools), selectinload(App.tags))
        .filter(App.id == app_id)
    )
    parent_app = result.scalars().first()
    if not parent_app:
        raise HTTPException(status_code=404, detail="Parent app not found")
    
    # Generate slug for fork
    base_slug = slugify(f"{parent_app.title}-fork")
    slug = generate_unique_slug(base_slug) # Always unique for forks likely

    # Simple fork: copy title and prompt and set parent
    db_app = App(
        creator_id=current_user.id,
        title=parent_app.title,
        prompt_text=parent_app.prompt_text,
        prd_text=parent_app.prd_text,
        extra_specs=parent_app.extra_specs,
        status=AppStatus.CONCEPT,
        parent_app_id=parent_app.id,
        slug=slug
    )
    
    # Inherit tools and tags? PRD doesn't specify, but often useful
    db_app.tools = parent_app.tools
    db_app.tags = parent_app.tags
    
    db.add(db_app)
    await db.commit()
    # Reload with eager loading
    result = await db.execute(
        select(App)
        .options(selectinload(App.tools), selectinload(App.tags), selectinload(App.media), selectinload(App.creator))
        .filter(App.id == db_app.id)
    )
    app = result.scalars().first()
    return app_to_schema(app, likes_count=0, comments_count=0, is_liked=False)

@router.post("/{app_id}/media", response_model=schemas.AppMedia)
async def add_app_media(
    app_id: int,
    media_in: schemas.AppMediaBase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(App).filter(App.id == app_id))
    db_app = result.scalars().first()
    if not db_app or db_app.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_media = AppMedia(**media_in.model_dump(), app_id=app_id)
    db.add(db_media)
    await db.commit()
    await db.refresh(db_media)
    return db_media

@router.delete("/{app_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app_media(
    app_id: int,
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify app exists and user is owner
    result = await db.execute(select(App).filter(App.id == app_id))
    db_app = result.scalars().first()
    if not db_app:
        raise HTTPException(status_code=404, detail="App not found")
    if db_app.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Find and delete the media
    result = await db.execute(
        select(AppMedia).filter(AppMedia.id == media_id, AppMedia.app_id == app_id)
    )
    db_media = result.scalars().first()
    if not db_media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    await db.delete(db_media)
    await db.commit()
    return None


# Dead App Report Endpoints
@router.post("/{app_id}/report-dead", response_model=schemas.DeadAppReport, status_code=status.HTTP_201_CREATED)
async def report_dead_app(
    app_id: int,
    report_in: schemas.DeadAppReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Report an app as dead/broken. Multiple users can report the same app."""
    # Check if app exists
    result = await db.execute(select(App).filter(App.id == app_id))
    db_app = result.scalars().first()
    if not db_app:
        raise HTTPException(status_code=404, detail="App not found")
    
    # Check if user already has a pending report for this app
    existing_result = await db.execute(
        select(DeadAppReport).filter(
            DeadAppReport.app_id == app_id,
            DeadAppReport.reporter_id == current_user.id,
            DeadAppReport.status == ReportStatus.PENDING
        )
    )
    if existing_result.scalars().first():
        raise HTTPException(
            status_code=400, 
            detail="You already have a pending report for this app"
        )
    
    db_report = DeadAppReport(
        app_id=app_id,
        reporter_id=current_user.id,
        reason=report_in.reason,
        status=ReportStatus.PENDING
    )
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    
    # Notify admin via Telegram
    notify_dead_link_report(current_user.username, db_app.title, report_in.reason)
    
    return db_report


@router.get("/dead-reports/pending", response_model=List[schemas.DeadAppReportWithDetails])
async def get_pending_dead_reports(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all pending dead app reports (admin only). Groups by app with report count."""
    # Get all pending reports with app and reporter details
    result = await db.execute(
        select(DeadAppReport)
        .options(selectinload(DeadAppReport.app), selectinload(DeadAppReport.reporter))
        .filter(DeadAppReport.status == ReportStatus.PENDING)
        .order_by(desc(DeadAppReport.created_at))
    )
    reports = result.scalars().all()
    
    # Count reports per app
    app_report_counts = {}
    for report in reports:
        app_report_counts[report.app_id] = app_report_counts.get(report.app_id, 0) + 1
    
    # Convert to response with report counts (return one report per app with count)
    seen_apps = set()
    response = []
    for report in reports:
        if report.app_id not in seen_apps:
            seen_apps.add(report.app_id)
            response.append({
                "id": report.id,
                "app_id": report.app_id,
                "reporter_id": report.reporter_id,
                "reason": report.reason,
                "status": report.status,
                "created_at": report.created_at,
                "resolved_at": report.resolved_at,
                "reporter": report.reporter,
                "app": report.app,
                "report_count": app_report_counts[report.app_id]
            })
    
    return response


@router.put("/dead-reports/{report_id}/resolve", response_model=schemas.DeadAppReport)
async def resolve_dead_report(
    report_id: int,
    resolve_in: schemas.DeadAppReportResolve,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Resolve a dead app report (admin only). If confirmed, marks the app as dead."""
    if resolve_in.status not in [ReportStatus.CONFIRMED, ReportStatus.DISMISSED]:
        raise HTTPException(
            status_code=400, 
            detail="Status must be 'confirmed' or 'dismissed'"
        )
    
    # Get the report
    result = await db.execute(
        select(DeadAppReport)
        .options(selectinload(DeadAppReport.app))
        .filter(DeadAppReport.id == report_id)
    )
    db_report = result.scalars().first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if db_report.status != ReportStatus.PENDING:
        raise HTTPException(status_code=400, detail="Report already resolved")
    
    # Update all pending reports for this app
    all_reports_result = await db.execute(
        select(DeadAppReport).filter(
            DeadAppReport.app_id == db_report.app_id,
            DeadAppReport.status == ReportStatus.PENDING
        )
    )
    all_reports = all_reports_result.scalars().all()
    
    for report in all_reports:
        report.status = resolve_in.status
        report.resolved_at = datetime.now()
    
    # If confirmed, mark the app as dead
    if resolve_in.status == ReportStatus.CONFIRMED:
        app_result = await db.execute(select(App).filter(App.id == db_report.app_id))
        db_app = app_result.scalars().first()
        if db_app:
            db_app.is_dead = True
    
    await db.commit()
    await db.refresh(db_report)
    return db_report
