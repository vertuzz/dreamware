"""Admin-only router for running the app submission agent."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.routers.auth import require_admin
from app.agent import run_agent, AgentDeps
from app.core.config import settings


router = APIRouter()


class AgentRunRequest(BaseModel):
    """Request body for running the agent."""
    prompt: str


class AgentRunResponse(BaseModel):
    """Response from running the agent."""
    success: bool
    result: str | None = None
    error: str | None = None
    app_ids: list[int] = []


@router.post("/agent/run", response_model=AgentRunResponse)
async def run_submission_agent(
    request: AgentRunRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Run the app submission agent with the provided prompt.
    
    Admin-only endpoint. The agent will:
    1. Parse the prompt (typically a Reddit/social media post about an app)
    2. Visit any app URLs mentioned
    3. Take screenshots
    4. Create a polished app listing
    5. Upload screenshots to S3
    
    Returns the result text and IDs of any created apps.
    """
    # Validate agent is configured
    if not settings.AGENT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not configured. Set AGENT_API_KEY environment variable.",
        )
    
    # Create agent dependencies
    deps = AgentDeps(
        db=db,
        user=admin_user,
        headless=settings.AGENT_HEADLESS,
    )
    
    # Run the agent
    result = await run_agent(request.prompt, deps)
    
    return AgentRunResponse(
        success=result.get("success", False),
        result=result.get("result"),
        error=result.get("error"),
        app_ids=result.get("app_ids", []),
    )


@router.get("/agent/status")
async def get_agent_status(
    admin_user: User = Depends(require_admin),
):
    """
    Check if the agent is configured and ready.
    
    Admin-only endpoint.
    """
    return {
        "configured": bool(settings.AGENT_API_KEY),
        "model": settings.AGENT_MODEL if settings.AGENT_API_KEY else None,
        "api_base": settings.AGENT_API_BASE if settings.AGENT_API_KEY else None,
        "headless": settings.AGENT_HEADLESS,
    }
