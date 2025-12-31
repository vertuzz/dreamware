from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, distinct
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models import Dream, User, Tool, Tag, DreamMedia, DreamStatus, Like, Comment, Review
from app.schemas import schemas
from app.routers.auth import get_current_user, get_current_user_optional
from app.utils import slugify, generate_unique_slug

router = APIRouter()


async def get_dream_counts(db: AsyncSession, dream_id: int) -> tuple[int, int]:
    """Get likes and comments counts for a single dream."""
    likes_result = await db.execute(
        select(func.count(Like.id)).filter(Like.dream_id == dream_id)
    )
    comments_result = await db.execute(
        select(func.count(Comment.id)).filter(Comment.dream_id == dream_id)
    )
    return likes_result.scalar() or 0, comments_result.scalar() or 0


def dream_to_schema(
    dream: Dream, 
    creator: Optional[schemas.DreamCreator] = None,
    likes_count: int = 0, 
    comments_count: int = 0,
    is_liked: bool = False
) -> schemas.Dream:
    """Convert Dream ORM object to dict with computed fields"""
    # Create the schema object directly
    return {
        "id": dream.id,
        "title": dream.title,
        "prompt_text": dream.prompt_text,
        "prd_text": dream.prd_text,
        "extra_specs": dream.extra_specs,
        "status": dream.status,
        "app_url": dream.app_url,
        "youtube_url": dream.youtube_url,
        "is_agent_submitted": dream.is_agent_submitted,
        "creator_id": dream.creator_id,
        "parent_dream_id": dream.parent_dream_id,
        "created_at": dream.created_at,
        "slug": dream.slug,
        "media": dream.media,
        "tools": dream.tools,
        "tags": dream.tags,
        "creator": creator or dream.creator,
        "likes_count": likes_count,
        "comments_count": comments_count,
        "is_liked": is_liked,
    }

@router.get("/", response_model=List[schemas.Dream])
async def get_dreams(
    skip: int = 0,
    limit: int = 20,
    tool_id: Optional[List[int]] = Query(None),
    tag_id: Optional[List[int]] = Query(None),
    tool: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[DreamStatus] = None,
    creator_id: Optional[int] = None,
    sort_by: str = Query("trending", enum=["trending", "newest", "top_rated", "likes"]),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    # Base query with eager loading of media, tools, tags and creator
    query = select(Dream).options(
        selectinload(Dream.tools), 
        selectinload(Dream.tags), 
        selectinload(Dream.media),
        selectinload(Dream.creator)
    )
    
    # 1. Joins for filtering and sorting
    if tool_id or tool:
        query = query.join(Dream.tools)
    if tag_id or tag:
        query = query.join(Dream.tags)
        
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
            (Dream.title.ilike(f"%{search}%")) |
            (Dream.prompt_text.ilike(f"%{search}%")) | 
            (Dream.prd_text.ilike(f"%{search}%"))
        )
        
    if status:
        query = query.filter(Dream.status == status)

    if creator_id:
        query = query.filter(Dream.creator_id == creator_id)
    
    # 3. Apply Sorting & Grouping
    # We always group by Dream.id to avoid duplicates from many-to-many joins
    query = query.group_by(Dream.id)
    
    if sort_by == "trending":
        # Trending = (Likes + Comments * 2) / (Age + 2)^1.8
        query = query.outerjoin(Dream.likes).outerjoin(Dream.comments)
        
        likes_count = func.count(distinct(Like.id))
        comments_count = func.count(distinct(Comment.id))
        
        # Handle SQLite vs Postgres for age calculation
        if db.bind.dialect.name == "sqlite":
            # julianday returns days, so multiply by 24 for hours
            age_in_hours = (func.julianday('now') - func.julianday(Dream.created_at)) * 24
        else:
            age_in_hours = func.extract('epoch', func.now() - Dream.created_at) / 3600
        
        # Gravity algorithm
        trending_score = (likes_count + (comments_count * 2) + 1) / func.power(age_in_hours + 2, 1.8)
        query = query.order_by(desc(trending_score), desc(Dream.id))
        
    elif sort_by == "top_rated":
        from app.models import Review
        query = query.outerjoin(Dream.reviews)
        # Average score, default to 0 if no reviews
        avg_score = func.coalesce(func.avg(Review.score), 0)
        query = query.order_by(desc(avg_score), desc(Dream.created_at), desc(Dream.id))
        
    elif sort_by == "likes":
        query = query.outerjoin(Dream.likes)
        query = query.order_by(desc(func.count(distinct(Like.id))), desc(Dream.created_at), desc(Dream.id))
        
    elif sort_by == "newest":
        query = query.order_by(desc(Dream.created_at), desc(Dream.id))
    
    else: # Default fallback to created_at
        query = query.order_by(desc(Dream.created_at), desc(Dream.id))
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    dreams = result.scalars().all()
    
    # Get counts for all dreams in a single query
    dream_ids = [d.id for d in dreams]
    
    if dream_ids:
        # Get likes counts
        likes_result = await db.execute(
            select(Like.dream_id, func.count(Like.id))
            .filter(Like.dream_id.in_(dream_ids))
            .group_by(Like.dream_id)
        )
        likes_map = dict(likes_result.all())
        
        # Get comments counts
        comments_result = await db.execute(
            select(Comment.dream_id, func.count(Comment.id))
            .filter(Comment.dream_id.in_(dream_ids))
            .group_by(Comment.dream_id)
        )
        comments_map = dict(comments_result.all())
    else:
        likes_map = {}
        comments_map = {}
    
    # Get liked status if user is logged in
    liked_dream_ids = set()
    if current_user:
        if dream_ids:
            likes_q = await db.execute(
                select(Like.dream_id)
                .filter(Like.dream_id.in_(dream_ids))
                .filter(Like.user_id == current_user.id)
            )
            liked_dream_ids = set(likes_q.scalars().all())

    # Convert to response with counts
    return [
        dream_to_schema(
            dream, 
            likes_count=likes_map.get(dream.id, 0),
            comments_count=comments_map.get(dream.id, 0),
            is_liked=(dream.id in liked_dream_ids)
        )
        for dream in dreams
    ]

@router.post("/", response_model=schemas.Dream)
async def create_dream(
    dream_in: schemas.DreamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    # Generate slug
    base_slug = slugify(dream_in.title)
    slug = base_slug
    
    # Check for uniqueness (simple loop for now, ideally handle with DB constraint exception)
    # Since we are in async, we can do a check.
    # Note: efficient way is to catch IntegrityError but for user feedback check is okay.
    existing = await db.execute(select(Dream).filter(Dream.slug == slug))
    if existing.scalar_one_or_none():
        slug = generate_unique_slug(base_slug)

    db_dream = Dream(
        creator_id=current_user.id,
        title=dream_in.title,
        prompt_text=dream_in.prompt_text,
        prd_text=dream_in.prd_text,
        extra_specs=dream_in.extra_specs,
        status=dream_in.status,
        app_url=dream_in.app_url,
        youtube_url=dream_in.youtube_url,
        is_agent_submitted=dream_in.is_agent_submitted,
        parent_dream_id=dream_in.parent_dream_id,
        slug=slug
    )
    
    # Add tools and tags
    if dream_in.tool_ids:
        result = await db.execute(select(Tool).filter(Tool.id.in_(dream_in.tool_ids)))
        tools = result.scalars().all()
        db_dream.tools = tools
    if dream_in.tag_ids:
        result = await db.execute(select(Tag).filter(Tag.id.in_(dream_in.tag_ids)))
        tags = result.scalars().all()
        db_dream.tags = tags
        
    db.add(db_dream)
    await db.commit()
    # Reload with eager loading
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.tools), selectinload(Dream.tags), selectinload(Dream.media), selectinload(Dream.creator))
        .filter(Dream.id == db_dream.id)
    )
    dream = result.scalars().first()
    return dream_to_schema(dream, likes_count=0, comments_count=0, is_liked=False)

@router.get("/{dream_identifier}", response_model=schemas.Dream)
async def get_dream(
    dream_identifier: str, 
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Try to parse as integer ID first
    dream_id = None
    if dream_identifier.isdigit():
        dream_id = int(dream_identifier)
        query = select(Dream).filter(Dream.id == dream_id)
    else:
        query = select(Dream).filter(Dream.slug == dream_identifier)

    result = await db.execute(
        query.options(selectinload(Dream.tools), selectinload(Dream.tags), selectinload(Dream.media), selectinload(Dream.creator))
    )
    dream = result.scalars().first()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    
    # Get counts
    likes_count, comments_count = await get_dream_counts(db, dream.id)
    
    # Check if liked
    is_liked = False
    if current_user:
        result_like = await db.execute(
            select(Like).filter(Like.dream_id == dream.id, Like.user_id == current_user.id)
        )
        if result_like.scalars().first():
            is_liked = True

    return dream_to_schema(dream, likes_count=likes_count, comments_count=comments_count, is_liked=is_liked)

@router.patch("/{dream_id}", response_model=schemas.Dream)
async def update_dream(
    dream_id: int,
    dream_in: schemas.DreamUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.tools), selectinload(Dream.tags), selectinload(Dream.media), selectinload(Dream.creator))
        .filter(Dream.id == dream_id)
    )
    db_dream = result.scalars().first()
    if not db_dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    if db_dream.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = dream_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_dream, field, value)
    
    db.add(db_dream)
    await db.commit()
    # Reload to ensure serialization works
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.tools), selectinload(Dream.tags), selectinload(Dream.media), selectinload(Dream.creator))
        .filter(Dream.id == db_dream.id)
    )
    dream = result.scalars().first()
    
    # Get counts
    likes_count, comments_count = await get_dream_counts(db, dream_id)
    
    return dream_to_schema(dream, likes_count=likes_count, comments_count=comments_count, is_liked=False) # User is creator, usually creators don't like their own dreams effectively or we can check. For now False or check.
    # Actually creator can like their own dream.
    # Let's check.
    result_like = await db.execute(
        select(Like).filter(Like.dream_id == dream.id, Like.user_id == current_user.id)
    )
    is_liked = result_like.scalars().first() is not None
    return dream_to_schema(dream, likes_count=likes_count, comments_count=comments_count, is_liked=is_liked)

@router.post("/{dream_id}/fork", response_model=schemas.Dream)
async def fork_dream(
    dream_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.tools), selectinload(Dream.tags))
        .filter(Dream.id == dream_id)
    )
    parent_dream = result.scalars().first()
    if not parent_dream:
        raise HTTPException(status_code=404, detail="Parent dream not found")
    
    # Generate slug for fork
    base_slug = slugify(f"{parent_dream.title}-fork")
    slug = generate_unique_slug(base_slug) # Always unique for forks likely

    # Simple fork: copy title and prompt and set parent
    db_dream = Dream(
        creator_id=current_user.id,
        title=parent_dream.title,
        prompt_text=parent_dream.prompt_text,
        prd_text=parent_dream.prd_text,
        extra_specs=parent_dream.extra_specs,
        status=DreamStatus.CONCEPT,
        parent_dream_id=parent_dream.id,
        slug=slug
    )
    
    # Inherit tools and tags? PRD doesn't specify, but often useful
    db_dream.tools = parent_dream.tools
    db_dream.tags = parent_dream.tags
    
    db.add(db_dream)
    await db.commit()
    # Reload with eager loading
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.tools), selectinload(Dream.tags), selectinload(Dream.media), selectinload(Dream.creator))
        .filter(Dream.id == db_dream.id)
    )
    dream = result.scalars().first()
    return dream_to_schema(dream, likes_count=0, comments_count=0, is_liked=False)

@router.post("/{dream_id}/media", response_model=schemas.DreamMedia)
async def add_dream_media(
    dream_id: int,
    media_in: schemas.DreamMediaBase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Dream).filter(Dream.id == dream_id))
    db_dream = result.scalars().first()
    if not db_dream or db_dream.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_media = DreamMedia(**media_in.model_dump(), dream_id=dream_id)
    db.add(db_media)
    await db.commit()
    await db.refresh(db_media)
    return db_media
