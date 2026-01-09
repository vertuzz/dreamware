from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Feedback, User
from app.schemas import schemas
from app.routers.auth import get_current_user
from app.services.telegram import notify_feedback

router = APIRouter()


@router.post("/feedback/", response_model=schemas.Feedback)
async def create_feedback(
    feedback_in: schemas.FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback (authenticated users only)."""
    feedback = Feedback(
        user_id=current_user.id,
        type=feedback_in.type,
        message=feedback_in.message
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    notify_feedback(current_user.username, feedback_in.type, feedback_in.message)
    return feedback


@router.get("/feedback/", response_model=List[schemas.FeedbackWithUser])
async def list_feedback(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all feedback (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    result = await db.execute(
        select(Feedback)
        .options(selectinload(Feedback.user))
        .order_by(Feedback.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete feedback (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    result = await db.execute(select(Feedback).filter(Feedback.id == feedback_id))
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found"
        )
    
    await db.delete(feedback)
    await db.commit()
