"""Dependencies for the Show Your App agent."""

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.core.config import settings


@dataclass
class AgentDeps:
    """Dependencies injected into the agent for database access and user context."""
    
    db: AsyncSession
    user: User
    headless: bool = field(default_factory=lambda: settings.AGENT_HEADLESS)
    
    # Cached context data (populated at bootstrap)
    tools_list: list[dict] = field(default_factory=list)
    tags_list: list[dict] = field(default_factory=list)
    user_apps: list[dict] = field(default_factory=list)
    
    # Track created app IDs during the run
    created_app_ids: list[int] = field(default_factory=list)
    
    # Browser instance (lazy initialized)
    _browser: Optional[object] = field(default=None, repr=False)
    _page: Optional[object] = field(default=None, repr=False)
