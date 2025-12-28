from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Tool, User
from app.schemas import schemas
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[schemas.Tool])
async def get_tools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tool))
    return result.scalars().all()

@router.post("/", response_model=schemas.Tool)
async def create_tool(
    tool_in: schemas.ToolBase, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create tools"
        )
    
    db_tool = Tool(name=tool_in.name)
    db.add(db_tool)
    await db.commit()
    await db.refresh(db_tool)
    return db_tool
