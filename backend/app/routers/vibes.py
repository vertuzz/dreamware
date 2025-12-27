from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.database import get_db
from app.models import Vibe, User, Tool, Tag, VibeImage, VibeStatus, vibe_tools, vibe_tags
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[schemas.Vibe])
def get_vibes(
    skip: int = 0,
    limit: int = 20,
    tool_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    tool: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[VibeStatus] = None,
    sort_by: str = Query("created_at", enum=["created_at", "score", "likes"]),
    db: Session = Depends(get_db)
):
    query = db.query(Vibe)
    
    if tool_id:
        query = query.join(Vibe.tools).filter(Tool.id == tool_id)
    elif tool:
        tool_names = [t.strip() for t in tool.split(",") if t.strip()]
        if len(tool_names) > 1:
            query = query.join(Vibe.tools).filter(Tool.name.in_(tool_names))
        else:
            query = query.join(Vibe.tools).filter(Tool.name.ilike(f"%{tool_names[0]}%"))
        
    if tag_id:
        query = query.join(Vibe.tags).filter(Tag.id == tag_id)
    elif tag:
        tag_names = [t.strip() for t in tag.split(",") if t.strip()]
        if len(tag_names) > 1:
            query = query.join(Vibe.tags).filter(Tag.name.in_(tag_names))
        else:
            query = query.join(Vibe.tags).filter(Tag.name.ilike(f"%{tag_names[0]}%"))
        
    if search:
        query = query.filter(
            (Vibe.prompt_text.ilike(f"%{search}%")) | 
            (Vibe.prd_text.ilike(f"%{search}%"))
        )
        
    if status:
        query = query.filter(Vibe.status == status)
    
    query = query.distinct()
    
    if sort_by == "created_at":
        query = query.order_by(desc(Vibe.created_at))
    # Note: sorting by score/likes would require joins or counter caches
        
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=schemas.Vibe)
def create_vibe(
    vibe_in: schemas.VibeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_vibe = Vibe(
        creator_id=current_user.id,
        prompt_text=vibe_in.prompt_text,
        prd_text=vibe_in.prd_text,
        extra_specs=vibe_in.extra_specs,
        status=vibe_in.status,
        parent_vibe_id=vibe_in.parent_vibe_id
    )
    
    # Add tools and tags
    if vibe_in.tool_ids:
        tools = db.query(Tool).filter(Tool.id.in_(vibe_in.tool_ids)).all()
        db_vibe.tools = tools
    if vibe_in.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(vibe_in.tag_ids)).all()
        db_vibe.tags = tags
        
    db.add(db_vibe)
    db.commit()
    db.refresh(db_vibe)
    return db_vibe

@router.get("/{vibe_id}", response_model=schemas.Vibe)
def get_vibe(vibe_id: int, db: Session = Depends(get_db)):
    vibe = db.query(Vibe).filter(Vibe.id == vibe_id).first()
    if not vibe:
        raise HTTPException(status_code=404, detail="Vibe not found")
    return vibe

@router.patch("/{vibe_id}", response_model=schemas.Vibe)
def update_vibe(
    vibe_id: int,
    vibe_in: schemas.VibeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_vibe = db.query(Vibe).filter(Vibe.id == vibe_id).first()
    if not db_vibe:
        raise HTTPException(status_code=404, detail="Vibe not found")
    if db_vibe.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = vibe_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vibe, field, value)
    
    db.add(db_vibe)
    db.commit()
    db.refresh(db_vibe)
    return db_vibe

@router.post("/{vibe_id}/fork", response_model=schemas.Vibe)
def fork_vibe(
    vibe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    parent_vibe = db.query(Vibe).filter(Vibe.id == vibe_id).first()
    if not parent_vibe:
        raise HTTPException(status_code=404, detail="Parent vibe not found")
    
    # Simple fork: copy prompt and set parent
    db_vibe = Vibe(
        creator_id=current_user.id,
        prompt_text=parent_vibe.prompt_text,
        prd_text=parent_vibe.prd_text,
        extra_specs=parent_vibe.extra_specs,
        status=VibeStatus.CONCEPT,
        parent_vibe_id=parent_vibe.id
    )
    
    # Inherit tools and tags? PRD doesn't specify, but often useful
    db_vibe.tools = parent_vibe.tools
    db_vibe.tags = parent_vibe.tags
    
    db.add(db_vibe)
    db.commit()
    db.refresh(db_vibe)
    return db_vibe

@router.post("/{vibe_id}/images", response_model=schemas.VibeImage)
def add_vibe_image(
    vibe_id: int,
    image_in: schemas.VibeImageBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_vibe = db.query(Vibe).filter(Vibe.id == vibe_id).first()
    if not db_vibe or db_vibe.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_image = VibeImage(**image_in.model_dump(), vibe_id=vibe_id)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image
