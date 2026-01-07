"""Tests for the Pydantic AI agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.deps import AgentDeps
from app.agent.tools import (
    get_available_tools,
    get_available_tags,
    get_my_apps,
    create_app,
    _generate_slug,
)
from app.models import User, Tool, Tag, App, AppStatus


class MockRunContext:
    """Mock RunContext for testing tools."""
    def __init__(self, deps: AgentDeps):
        self.deps = deps


@pytest.fixture
def mock_user():
    """Create a mock admin user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "admin"
    user.email = "admin@test.com"
    user.is_admin = True
    return user


@pytest.fixture
def mock_db():
    """Create a mock async database session."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def agent_deps(mock_db, mock_user):
    """Create agent dependencies for testing."""
    return AgentDeps(
        db=mock_db,
        user=mock_user,
        headless=True,
    )


class TestGenerateSlug:
    """Tests for slug generation."""
    
    def test_simple_title(self):
        assert _generate_slug("My App") == "my-app"
    
    def test_special_characters(self):
        assert _generate_slug("PixelPet - AI Companion!") == "pixelpet-ai-companion"
    
    def test_multiple_spaces(self):
        assert _generate_slug("My   Cool   App") == "my-cool-app"
    
    def test_long_title(self):
        long_title = "A" * 200
        assert len(_generate_slug(long_title)) <= 100


class TestGetAvailableTools:
    """Tests for get_available_tools function."""
    
    @pytest.mark.asyncio
    async def test_returns_cached_tools(self, agent_deps):
        """Should return cached tools if already populated."""
        agent_deps.tools_list = [{"id": 1, "name": "Cursor"}]
        ctx = MockRunContext(agent_deps)
        
        result = await get_available_tools(ctx)
        
        assert result == [{"id": 1, "name": "Cursor"}]
        agent_deps.db.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_fetches_from_db(self, agent_deps):
        """Should fetch tools from DB if not cached."""
        mock_tool = MagicMock(spec=Tool)
        mock_tool.id = 1
        mock_tool.name = "Claude Code"
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_tool]
        agent_deps.db.execute.return_value = mock_result
        
        ctx = MockRunContext(agent_deps)
        result = await get_available_tools(ctx)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Claude Code"
        agent_deps.db.execute.assert_called_once()


class TestGetAvailableTags:
    """Tests for get_available_tags function."""
    
    @pytest.mark.asyncio
    async def test_returns_cached_tags(self, agent_deps):
        """Should return cached tags if already populated."""
        agent_deps.tags_list = [{"id": 1, "name": "AI-Powered"}]
        ctx = MockRunContext(agent_deps)
        
        result = await get_available_tags(ctx)
        
        assert result == [{"id": 1, "name": "AI-Powered"}]
        agent_deps.db.execute.assert_not_called()


class TestCreateApp:
    """Tests for create_app function."""
    
    @pytest.mark.asyncio
    async def test_invalid_status(self, agent_deps):
        """Should return error for invalid status."""
        ctx = MockRunContext(agent_deps)
        
        result = await create_app(
            ctx,
            title="Test App",
            prompt_text="A test app",
            prd_text="<p>Description</p>",
            status="Invalid",
            tool_ids=[],
            tag_ids=[],
        )
        
        assert "error" in result
        assert "Invalid status" in result["error"]
    
    @pytest.mark.asyncio
    async def test_live_requires_app_url(self, agent_deps):
        """Should require app_url for Live status."""
        ctx = MockRunContext(agent_deps)
        
        result = await create_app(
            ctx,
            title="Test App",
            prompt_text="A test app",
            prd_text="<p>Description</p>",
            status="Live",
            tool_ids=[],
            tag_ids=[],
            app_url=None,
        )
        
        assert "error" in result
        assert "app_url is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_successful_creation(self, agent_deps):
        """Should create app successfully."""
        # Mock slug uniqueness check
        mock_result = MagicMock()
        mock_result.scalar.return_value = None  # No existing app with slug
        agent_deps.db.execute.return_value = mock_result
        
        ctx = MockRunContext(agent_deps)
        
        result = await create_app(
            ctx,
            title="Test App",
            prompt_text="A test app",
            prd_text="<p>Description</p>",
            status="Concept",
            tool_ids=[],
            tag_ids=[],
        )
        
        assert result.get("success") is True
        assert "app_id" in result
        assert agent_deps.db.add.called
        assert agent_deps.db.flush.called


class TestAgentRouter:
    """Tests for the agent router endpoints."""
    
    @pytest.mark.asyncio
    async def test_agent_status_requires_admin(self, client, auth_headers):
        """Non-admin users should not access agent status."""
        response = await client.get(
            "/agent/status",
            headers=auth_headers,
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_agent_run_requires_admin(self, client, auth_headers):
        """Non-admin users should not run the agent."""
        response = await client.post(
            "/agent/run",
            json={"prompt": "Test prompt"},
            headers=auth_headers,
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_agent_status_admin_access(self, client, admin_headers):
        """Admin users should access agent status."""
        response = await client.get(
            "/agent/status",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert "model" in data
