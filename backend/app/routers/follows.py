from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List

from app.database import get_db
from app.models import User, Follow, Notification, NotificationType
from app.routers.auth import get_current_user
from app.services.reputation import update_reputation, FOLLOW_POINTS

router = APIRouter()

@router.get("/{user_id}/follow/status")
async def get_follow_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if the current user is following the target user."""
    result = await db.execute(
        select(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.followed_id == user_id
        )
    )
    follow = result.scalars().first()
    return {"is_following": follow is not None}

@router.post("/{user_id}/follow")
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
        
    result = await db.execute(select(User).filter(User.id == user_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
        
    db_follow = Follow(follower_id=current_user.id, followed_id=user_id)
    db.add(db_follow)

    # Create notification
    notification = Notification(
        user_id=user_id,
        type=NotificationType.FOLLOW,
        content=f"{current_user.username} followed you",
        link=f"/users/{current_user.username}",
        is_read=False
    )
    db.add(notification)
    
    try:
        await db.commit()
        # Update target user's reputation
        await update_reputation(db, user_id, FOLLOW_POINTS)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Already following")
        
    return {"message": f"Following {target.username}"}

@router.delete("/{user_id}/follow")
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.followed_id == user_id
        )
    )
    db_follow = result.scalars().first()
    if not db_follow:
        raise HTTPException(status_code=404, detail="Not following this user")
        
    await db.delete(db_follow)
    await db.commit()
    
    # Update target user's reputation
    await update_reputation(db, user_id, -FOLLOW_POINTS)
    await db.commit()
    
    return {"message": "Unfollowed"}
