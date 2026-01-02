from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Like, User, Dream, Comment, Notification, NotificationType
from app.routers.auth import get_current_user
from app.services.reputation import update_reputation, LIKE_POINTS

router = APIRouter()

@router.post("/dreams/{dream_id}/like")
async def like_dream(
    dream_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Dream).filter(Dream.id == dream_id))
    dream = result.scalars().first()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    
    db_like = Like(dream_id=dream_id, user_id=current_user.id)
    db.add(db_like)
    
    try:
        await db.commit()
        # Notify
        if dream.creator_id != current_user.id:
            notification = Notification(
                user_id=dream.creator_id,
                type=NotificationType.LIKE,
                content=f"{current_user.username} liked your dream",
                link=f"/dreams/{dream_id}"
            )
            db.add(notification)
            await db.commit()
            
            # Update dream creator's reputation
            await update_reputation(db, dream.creator_id, LIKE_POINTS)
            await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Already liked")
    
    return {"message": "Liked"}

@router.delete("/dreams/{dream_id}/like")
async def unlike_dream(
    dream_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Like).filter(Like.dream_id == dream_id, Like.user_id == current_user.id))
    db_like = result.scalars().first()
    if not db_like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    # Get dream to find creator for reputation update
    result_dream = await db.execute(select(Dream).filter(Dream.id == dream_id))
    dream = result_dream.scalars().first()
    
    await db.delete(db_like)
    await db.commit()
    
    if dream and dream.creator_id != current_user.id:
        await update_reputation(db, dream.creator_id, -LIKE_POINTS)
        await db.commit()
        
    return {"message": "Unliked"}

