from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.models import User

# Point Constants
LIKE_POINTS = 2
COMMENT_VOTE_POINTS = 1
FOLLOW_POINTS = 5

async def update_reputation(db: AsyncSession, user_id: int, delta: int) -> None:
    """
    Update a user's reputation score by a given delta.
    The delta can be positive or negative.
    """
    if delta == 0:
        return
        
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(reputation_score=User.reputation_score + delta)
    )
    # We don't commit here to allow the caller to handle the transaction
