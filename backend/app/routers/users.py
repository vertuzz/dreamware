from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models import User, UserLink
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/{user_id}", response_model=schemas.UserPublic)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).options(selectinload(User.links)).filter(User.id == user_id)
    )
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: int, 
    user_in: schemas.UserUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    await db.commit()
    # Reload with eager loading
    result = await db.execute(
        select(User).options(selectinload(User.links)).filter(User.id == current_user.id)
    )
    return result.scalars().first()

@router.post("/{user_id}/links", response_model=schemas.UserLink)
async def create_user_link(
    user_id: int,
    link_in: schemas.UserLinkBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_link = UserLink(**link_in.model_dump(), user_id=user_id)
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link

@router.delete("/{user_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_link(
    user_id: int,
    link_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(select(UserLink).filter(UserLink.id == link_id, UserLink.user_id == user_id))
    db_link = result.scalars().first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    await db.delete(db_link)
    await db.commit()
    return None
