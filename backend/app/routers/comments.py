from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models import Comment, User, Dream, Notification, NotificationType, CommentVote
from app.schemas import schemas
from app.routers.auth import get_current_user, get_current_user_optional
from app.services.reputation import update_reputation, COMMENT_VOTE_POINTS

router = APIRouter()

@router.get("/dreams/{dream_id}/comments", response_model=List[schemas.CommentWithUser])
async def get_dream_comments(
    dream_id: int, 
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    # Fetch comments
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .filter(Comment.dream_id == dream_id)
        .order_by(Comment.created_at.desc())
    )
    comments = result.scalars().all()
    
    # If user is logged in, fetch their votes
    user_votes = {}
    if current_user:
        votes_result = await db.execute(
            select(CommentVote)
            .filter(
                CommentVote.user_id == current_user.id,
                CommentVote.comment_id.in_([c.id for c in comments])
            )
        )
        for vote in votes_result.scalars():
            user_votes[vote.comment_id] = vote.value

    # Attach vote status to comments
    # Note: Pydantic model expects user_vote, so we need to set it manually or map it
    comments_with_votes = []
    for comment in comments:
        # We need to ensure we return objects that match the schema
        # Since SQLAlchemy objects might not let us set arbitrary attributes easily if not in model,
        # we can just attach it and hope Pydantic's from_attributes handles it, 
        # OR better: construct a dictionary or copy.
        # However, relying on object identity for relations (user) implies keeping the object.
        # Let's try setting the attribute directly. Python allows this on instances.
        comment.user_vote = user_votes.get(comment.id, 0)
        comments_with_votes.append(comment)

    return comments_with_votes

@router.post("/dreams/{dream_id}/comments", response_model=schemas.Comment)
async def create_comment(
    dream_id: int,
    comment_in: schemas.CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify dream exists
    result = await db.execute(select(Dream).filter(Dream.id == dream_id))
    dream = result.scalars().first()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    
    # If parent_id provided, verify it exists and belongs to same dream
    if comment_in.parent_id:
        parent_res = await db.execute(select(Comment).filter(Comment.id == comment_in.parent_id))
        parent = parent_res.scalars().first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        if parent.dream_id != dream_id:
            raise HTTPException(status_code=400, detail="Parent comment belongs to a different dream")
    
    db_comment = Comment(
        dream_id=dream_id,
        user_id=current_user.id,
        content=comment_in.content,
        parent_id=comment_in.parent_id
    )
    db.add(db_comment)
    
    # Notify creator (only if top-level or if replying to someone else? For now just notify dream creator)
    # Refinement: If it's a reply, maybe notify the parent comment's author too?
    # Simple version first: Notify dream creator if not them.
    if dream.creator_id != current_user.id:
        notification = Notification(
            user_id=dream.creator_id,
            type=NotificationType.COMMENT,
            content=f"{current_user.username} commented on your dream",
            link=f"/dreams/{dream_id}"
        )
        db.add(notification)
    
    # Notify parent comment author if it's a reply and not their own comment
    if comment_in.parent_id:
        parent_res = await db.execute(select(Comment).filter(Comment.id == comment_in.parent_id))
        parent = parent_res.scalars().first()
        if parent and parent.user_id != current_user.id and parent.user_id != dream.creator_id:
             # Avoid double notification if dream creator is parent author
             notification = Notification(
                user_id=parent.user_id,
                type=NotificationType.COMMENT,
                content=f"{current_user.username} replied to your comment",
                link=f"/dreams/{dream_id}"
            )
             db.add(notification)

    await db.commit()
    await db.refresh(db_comment)
    db_comment.user_vote = 0 # New comment has no vote from creator yet
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
    
    # Fetch user vote to return correct schema
    vote_res = await db.execute(select(CommentVote).filter(
        CommentVote.comment_id == comment_id, CommentVote.user_id == current_user.id
    ))
    vote = vote_res.scalars().first()
    db_comment.user_vote = vote.value if vote else 0
    
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

@router.post("/comments/{comment_id}/vote")
async def vote_comment(
    comment_id: int,
    value: int, # Query param? Or body? Let's use query param for simplicity or body if strictly REST. 
                # Better: POST body. But this runs via query param by default in FastAPI if not typed as schema.
                # Let's accept value as query param for valid values: 1, -1, 0 (remove vote).
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if value not in [1, -1, 0]:
         raise HTTPException(status_code=400, detail="Invalid vote value")

    result = await db.execute(select(Comment).filter(Comment.id == comment_id))
    comment = result.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check existing vote
    vote_res = await db.execute(select(CommentVote).filter(
        CommentVote.comment_id == comment_id,
        CommentVote.user_id == current_user.id
    ))
    existing_vote = vote_res.scalars().first()
    
    # Calculate score change
    score_delta = 0
    
    if existing_vote:
        if value == 0:
            # Remove vote
            score_delta = -existing_vote.value
            await db.delete(existing_vote)
        elif value != existing_vote.value:
            # Change vote
            score_delta = value - existing_vote.value
            existing_vote.value = value
            db.add(existing_vote)
        else:
            # Same vote, do nothing (or toggle off? typically API expects explicit state)
            pass
    elif value != 0:
        # New vote
        new_vote = CommentVote(comment_id=comment_id, user_id=current_user.id, value=value)
        db.add(new_vote)
        score_delta = value
        
    if score_delta != 0:
        comment.score += score_delta
        db.add(comment)
        
        # Update comment author's reputation (if not self-voting)
        if comment.user_id != current_user.id:
            await update_reputation(db, comment.user_id, score_delta * COMMENT_VOTE_POINTS)
        
    await db.commit()
    
    return {"message": "Vote recorded", "score": comment.score}
