from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models import Comment, User, Dream, Notification, NotificationType
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/dreams/{dream_id}/comments", response_model=List[schemas.CommentWithUser])
async def get_dream_comments(dream_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .filter(Comment.dream_id == dream_id)
        .order_by(Comment.created_at.desc())
    )
    return result.scalars().all()

@router.post("/dreams/{dream_id}/comments", response_model=schemas.Comment)
async def create_comment(
    dream_id: int,
    comment_in: schemas.CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Dream).filter(Dream.id == dream_id))
    dream = result.scalars().first()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    
    db_comment = Comment(
        dream_id=dream_id,
        user_id=current_user.id,
        content=comment_in.content
    )
    db.add(db_comment)
    
    # Notify creator
    if dream.creator_id != current_user.id:
        notification = Notification(
            user_id=dream.creator_id,
            type=NotificationType.COMMENT,
            content=f"{current_user.username} commented on your dream",
            link=f"/dreams/{dream_id}"
        )
        db.add(notification)
        
    await db.commit()
    await db.refresh(db_comment)
    return db_comment

@router.patch("/comments/{comment_id}", response_model=schemas.Comment)
async def update_comment(
    comment_id: int,
    comment_in: schemas.CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Comment).filter(Comment.id == comment_id))
    db_comment = result.scalars().first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if db_comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_comment.content = comment_in.content
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Comment).filter(Comment.id == comment_id))
    db_comment = result.scalars().first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if db_comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.delete(db_comment)
    await db.commit()
    return None
