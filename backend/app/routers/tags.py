from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Tag, User
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[schemas.Tag])
async def get_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag))
    return result.scalars().all()

@router.post("/", response_model=schemas.Tag)
async def create_tag(
    tag_in: schemas.TagBase, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != 1:
        raise HTTPException(
            status_code=403,
            detail="Only admin can create tags"
        )
    
    db_tag = Tag(name=tag_in.name)
    db.add(db_tag)
    await db.commit()
    await db.refresh(db_tag)
    return db_tag
