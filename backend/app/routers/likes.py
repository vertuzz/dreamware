from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Like, User, App, Comment, Notification, NotificationType
from app.routers.auth import get_current_user
from app.services.reputation import update_reputation, LIKE_POINTS
from app.services.telegram import notify_like

router = APIRouter()

@router.post("/apps/{app_id}/like")
async def like_app(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(App).filter(App.id == app_id))
    app = result.scalars().first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    db_like = Like(app_id=app_id, user_id=current_user.id)
    db.add(db_like)
    
    try:
        await db.commit()
        notify_like(current_user.username, app.title)
        # Notify
        if app.creator_id != current_user.id:
            notification = Notification(
                user_id=app.creator_id,
                type=NotificationType.LIKE,
                content=f"{current_user.username} liked your app",
                link=f"/apps/{app_id}"
            )
            db.add(notification)
            await db.commit()
            
            # Update app creator's reputation
            await update_reputation(db, app.creator_id, LIKE_POINTS)
            await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Already liked")
    
    return {"message": "Liked"}

@router.delete("/apps/{app_id}/like")
async def unlike_app(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Like).filter(Like.app_id == app_id, Like.user_id == current_user.id))
    db_like = result.scalars().first()
    if not db_like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    # Get app to find creator for reputation update
    result_app = await db.execute(select(App).filter(App.id == app_id))
    app = result_app.scalars().first()
    
    await db.delete(db_like)
    await db.commit()
    
    if app and app.creator_id != current_user.id:
        await update_reputation(db, app.creator_id, -LIKE_POINTS)
        await db.commit()
        
    return {"message": "Unliked"}

