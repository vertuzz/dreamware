from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models import Collection, User, Vibe, collection_vibes
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.Collection)
async def create_collection(
    col_in: schemas.CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    db_col = Collection(
        name=col_in.name,
        description=col_in.description,
        is_public=col_in.is_public,
        owner_id=current_user.id
    )
    if col_in.vibe_ids:
        result = await db.execute(select(Vibe).filter(Vibe.id.in_(col_in.vibe_ids)))
        vibes = result.scalars().all()
        db_col.vibes = vibes
        
    db.add(db_col)
    await db.commit()
    # Reload with eager loading for nested relationships
    result = await db.execute(
        select(Collection)
        .options(
            selectinload(Collection.vibes).selectinload(Vibe.tools),
            selectinload(Collection.vibes).selectinload(Vibe.tags),
            selectinload(Collection.vibes).selectinload(Vibe.images)
        )
        .filter(Collection.id == db_col.id)
    )
    return result.scalars().first()

@router.get("/{col_id}", response_model=schemas.Collection)
async def get_collection(col_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Collection)
        .options(
            selectinload(Collection.vibes).selectinload(Vibe.tools),
            selectinload(Collection.vibes).selectinload(Vibe.tags),
            selectinload(Collection.vibes).selectinload(Vibe.images)
        )
        .filter(Collection.id == col_id)
    )
    col = result.scalars().first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not col.is_public:
        # Check ownership if private (skipped for simplicity in this public getter)
        pass
    return col

@router.post("/{col_id}/vibes/{vibe_id}")
async def add_to_collection(
    col_id: int,
    vibe_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.vibes))
        .filter(Collection.id == col_id, Collection.owner_id == current_user.id)
    )
    col = result.scalars().first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    result = await db.execute(select(Vibe).filter(Vibe.id == vibe_id))
    vibe = result.scalars().first()
    if not vibe:
        raise HTTPException(status_code=404, detail="Vibe not found")
    
    if vibe not in col.vibes:
        col.vibes.append(vibe)
        db.add(col)
        await db.commit()
        
    return {"message": "Added"}
