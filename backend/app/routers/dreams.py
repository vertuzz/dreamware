from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, distinct
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models import Dream, User, Tool, Tag, DreamMedia, DreamStatus, dream_tools, dream_tags
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[schemas.Dream])
async def get_dreams(
    skip: int = 0,
    limit: int = 20,
    tool_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    tool: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[DreamStatus] = None,
    sort_by: str = Query("trending", enum=["trending", "newest", "top_rated", "likes"]),
    db: AsyncSession = Depends(get_db)
):
    # Base query with eager loading of media, tools, and tags
    query = select(Dream).options(
        selectinload(Dream.tools), 
        selectinload(Dream.tags), 
        selectinload(Dream.media)
    )
    
    # 1. Joins for filtering and sorting
    if tool_id or tool:
        query = query.join(Dream.tools)
    if tag_id or tag:
        query = query.join(Dream.tags)
        
    # 2. Apply Filters
    if tool_id:
        query = query.filter(Tool.id == tool_id)
    elif tool:
        tool_names = [t.strip() for t in tool.split(",") if t.strip()]
        if len(tool_names) > 1:
            query = query.filter(Tool.name.in_(tool_names))
        else:
            query = query.filter(Tool.name.ilike(f"%{tool_names[0]}%"))
        
    if tag_id:
        query = query.filter(Tag.id == tag_id)
    elif tag:
        tag_names = [t.strip() for t in tag.split(",") if t.strip()]
        if len(tag_names) > 1:
            query = query.filter(Tag.name.in_(tag_names))
        else:
            query = query.filter(Tag.name.ilike(f"%{tag_names[0]}%"))
        
    if search:
        query = query.filter(
            (Dream.prompt_text.ilike(f"%{search}%")) | 
            (Dream.prd_text.ilike(f"%{search}%"))
        )
        
    if status:
        query = query.filter(Dream.status == status)
    
    # 3. Apply Sorting & Grouping
    # We always group by Dream.id to avoid duplicates from many-to-many joins
    query = query.group_by(Dream.id)
    
    if sort_by == "trending":
        # Trending = (Likes + Comments * 2) / (Age + 2)^1.8
        from app.models import Like, Comment
        query = query.outerjoin(Dream.likes).outerjoin(Dream.comments)
        
        likes_count = func.count(distinct(Like.id))
        comments_count = func.count(distinct(Comment.id))
        age_in_hours = func.extract('epoch', func.now() - Dream.created_at) / 3600
        
        # Gravity algorithm
        trending_score = (likes_count + (comments_count * 2) + 1) / func.power(age_in_hours + 2, 1.8)
        query = query.order_by(desc(trending_score))
        
    elif sort_by == "top_rated":
        from app.models import Review
        query = query.outerjoin(Dream.reviews)
        # Average score, default to 0 if no reviews
        avg_score = func.coalesce(func.avg(Review.score), 0)
        query = query.order_by(desc(avg_score), desc(Dream.created_at))
        
    elif sort_by == "likes":
        from app.models import Like
        query = query.outerjoin(Dream.likes)
        query = query.order_by(desc(func.count(distinct(Like.id))), desc(Dream.created_at))
        
    elif sort_by == "newest":
        query = query.order_by(desc(Dream.created_at))
    
    else: # Default fallback to created_at
        query = query.order_by(desc(Dream.created_at))
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=schemas.Dream)
async def create_dream(
    dream_in: schemas.DreamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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
        parent_dream_id=dream_in.parent_dream_id
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
        .options(selectinload(Dream.tools), selectinload(Dream.tags), selectinload(Dream.media))
        .filter(Dream.id == db_dream.id)
    )
    return result.scalars().first()

@router.get("/{dream_id}", response_model=schemas.Dream)
async def get_dream(dream_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.tools), selectinload(Dream.tags), selectinload(Dream.media))
        .filter(Dream.id == dream_id)
    )
    dream = result.scalars().first()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    return dream

@router.patch("/{dream_id}", response_model=schemas.Dream)
async def update_dream(
    dream_id: int,
    dream_in: schemas.DreamUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.tools), selectinload(Dream.tags), selectinload(Dream.media))
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
        .options(selectinload(Dream.tools), selectinload(Dream.tags), selectinload(Dream.media))
        .filter(Dream.id == db_dream.id)
    )
    return result.scalars().first()

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
    
    # Simple fork: copy title and prompt and set parent
    db_dream = Dream(
        creator_id=current_user.id,
        title=parent_dream.title,
        prompt_text=parent_dream.prompt_text,
        prd_text=parent_dream.prd_text,
        extra_specs=parent_dream.extra_specs,
        status=DreamStatus.CONCEPT,
        parent_dream_id=parent_dream.id
    )
    
    # Inherit tools and tags? PRD doesn't specify, but often useful
    db_dream.tools = parent_dream.tools
    db_dream.tags = parent_dream.tags
    
    db.add(db_dream)
    await db.commit()
    # Reload with eager loading
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.tools), selectinload(Dream.tags), selectinload(Dream.media))
        .filter(Dream.id == db_dream.id)
    )
    return result.scalars().first()

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
