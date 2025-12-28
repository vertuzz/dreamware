from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Implementation, User, Dream, Notification, NotificationType
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/dreams/{dream_id}/implementations", response_model=List[schemas.Implementation])
async def get_dream_implementations(dream_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Implementation).filter(Implementation.dream_id == dream_id))
    return result.scalars().all()

@router.post("/dreams/{dream_id}/implementations", response_model=schemas.Implementation)
async def create_implementation(
    dream_id: int,
    impl_in: schemas.ImplementationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Dream).filter(Dream.id == dream_id))
    dream = result.scalars().first()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    
    db_impl = Implementation(
        dream_id=dream_id,
        user_id=current_user.id,
        **impl_in.model_dump()
    )
    db.add(db_impl)
    
    # Notify creator
    if dream.creator_id != current_user.id:
        notification = Notification(
            user_id=dream.creator_id,
            type=NotificationType.IMPLEMENTATION,
            content=f"{current_user.username} submitted an implementation for your dream",
            link=f"/dreams/{dream_id}"
        )
        db.add(notification)
        
    await db.commit()
    await db.refresh(db_impl)
    return db_impl

@router.patch("/implementations/{impl_id}/official", response_model=schemas.Implementation)
async def mark_official(
    impl_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Implementation).filter(Implementation.id == impl_id))
    impl = result.scalars().first()
    if not impl:
        raise HTTPException(status_code=404, detail="Implementation not found")
    
    result = await db.execute(select(Dream).filter(Dream.id == impl.dream_id))
    dream = result.scalars().first()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    if dream.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only dream creator can mark implementation as official")
    
    # Unmark others as official for this dream
    result = await db.execute(
        select(Implementation).filter(
            Implementation.dream_id == dream.id, 
            Implementation.is_official == True
        )
    )
    for other_impl in result.scalars().all():
        other_impl.is_official = False
        db.add(other_impl)
    
    impl.is_official = True
    db.add(impl)
    await db.commit()
    await db.refresh(impl)
    return impl
