"""Tests for the Pydantic AI agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.deps import AgentDeps
from app.agent.tools import (
    get_tags_and_tools,
    get_my_apps,
    search_apps,
    create_app,
    _generate_slug,
    _check_browser_limit,
    MAX_BROWSER_STEPS,
)
from app.models import User, Tool, Tag, App, AppStatus
from app.utils import normalize_url


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


class TestBrowserStepLimit:
    """Tests for browser step limiting."""
    
    def test_browser_limit_not_reached(self, agent_deps):
        """Should allow browser calls when under limit."""
        agent_deps.browser_step_count = 5
        ctx = MockRunContext(agent_deps)
        
        result = _check_browser_limit(ctx)
        
        assert result is None
        assert agent_deps.browser_step_count == 6
    
    def test_browser_limit_reached(self, agent_deps):
        """Should return error when limit reached."""
        agent_deps.browser_step_count = MAX_BROWSER_STEPS
        ctx = MockRunContext(agent_deps)
        
        result = _check_browser_limit(ctx)
        
        assert result is not None
        assert "error" in result
        assert "Browser step limit" in result["error"]
        # Count should not increment when limit reached
        assert agent_deps.browser_step_count == MAX_BROWSER_STEPS
    
    def test_max_browser_steps_is_10(self):
        """Verify MAX_BROWSER_STEPS is set to 10."""
        assert MAX_BROWSER_STEPS == 10


class TestGetTagsAndTools:
    """Tests for get_tags_and_tools function."""
    
    @pytest.mark.asyncio
    async def test_returns_cached_data(self, agent_deps):
        """Should return cached data if already populated."""
        agent_deps.tools_list = [{"id": 1, "name": "Cursor"}]
        agent_deps.tags_list = [{"id": 1, "name": "AI-Powered"}]
        ctx = MockRunContext(agent_deps)
        
        result = await get_tags_and_tools(ctx)
        
        assert result["tools"] == [{"id": 1, "name": "Cursor"}]
        assert result["tags"] == [{"id": 1, "name": "AI-Powered"}]
        agent_deps.db.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_fetches_from_db(self, agent_deps):
        """Should fetch both tools and tags from DB if not cached."""
        mock_tool = MagicMock(spec=Tool)
        mock_tool.id = 1
        mock_tool.name = "Claude Code"
        
        mock_tag = MagicMock(spec=Tag)
        mock_tag.id = 1
        mock_tag.name = "AI-Powered"
        
        # First call returns tools, second returns tags
        mock_result_tools = MagicMock()
        mock_result_tools.scalars.return_value.all.return_value = [mock_tool]
        
        mock_result_tags = MagicMock()
        mock_result_tags.scalars.return_value.all.return_value = [mock_tag]
        
        agent_deps.db.execute.side_effect = [mock_result_tools, mock_result_tags]
        
        ctx = MockRunContext(agent_deps)
        result = await get_tags_and_tools(ctx)
        
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "Claude Code"
        assert len(result["tags"]) == 1
        assert result["tags"][0]["name"] == "AI-Powered"
        assert agent_deps.db.execute.call_count == 2


class TestNormalizeUrl:
    """Tests for URL normalization utility."""
    
    def test_strips_https_protocol(self):
        assert normalize_url("https://example.com") == "example.com"
    
    def test_strips_http_protocol(self):
        assert normalize_url("http://example.com") == "example.com"
    
    def test_strips_www_prefix(self):
        assert normalize_url("https://www.example.com") == "example.com"
    
    def test_removes_trailing_slash(self):
        assert normalize_url("https://example.com/") == "example.com"
    
    def test_preserves_path(self):
        assert normalize_url("https://example.com/path/to/page") == "example.com/path/to/page"
    
    def test_lowercases_url(self):
        assert normalize_url("https://EXAMPLE.COM/PATH") == "example.com/path"
    
    def test_handles_no_protocol(self):
        assert normalize_url("example.com/app") == "example.com/app"
    
    def test_preserves_query_params(self):
        assert normalize_url("https://example.com/page?id=123") == "example.com/page?id=123"
    
    def test_returns_none_for_empty(self):
        assert normalize_url("") is None
        assert normalize_url(None) is None
    
    def test_complex_url(self):
        url = "https://www.my-app.example.com/dashboard/"
        assert normalize_url(url) == "my-app.example.com/dashboard"


class TestSearchApps:
    """Tests for search_apps function (platform-wide duplicate detection)."""
    
    @pytest.mark.asyncio
    async def test_requires_url_or_title(self, agent_deps):
        """Should return error if neither url nor title provided."""
        ctx = MockRunContext(agent_deps)
        
        result = await search_apps(ctx, url=None, title=None)
        
        assert "error" in result
        assert "Must provide either url or title" in result["error"]
    
    @pytest.mark.asyncio
    async def test_search_by_url(self, agent_deps):
        """Should search apps by normalized URL."""
        # Create a mock app with creator
        mock_creator = MagicMock(spec=User)
        mock_creator.id = 2
        mock_creator.username = "other_user"
        
        mock_app = MagicMock(spec=App)
        mock_app.id = 42
        mock_app.title = "Cool App"
        mock_app.slug = "cool-app"
        mock_app.status = AppStatus.LIVE
        mock_app.app_url = "https://www.coolapp.com/"
        mock_app.creator_id = 2
        mock_app.creator = mock_creator
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_app]
        agent_deps.db.execute.return_value = mock_result
        
        ctx = MockRunContext(agent_deps)
        result = await search_apps(ctx, url="https://coolapp.com")
        
        assert len(result) == 1
        assert result[0]["id"] == 42
        assert result[0]["title"] == "Cool App"
        assert result[0]["app_url"] == "https://www.coolapp.com/"
        assert result[0]["is_mine"] is False  # Different creator
        assert result[0]["creator"]["username"] == "other_user"
    
    @pytest.mark.asyncio
    async def test_search_by_title(self, agent_deps):
        """Should search apps by title with fuzzy matching."""
        mock_creator = MagicMock(spec=User)
        mock_creator.id = 1  # Same as mock_user
        mock_creator.username = "admin"
        
        mock_app = MagicMock(spec=App)
        mock_app.id = 10
        mock_app.title = "My Weather App"
        mock_app.slug = "my-weather-app"
        mock_app.status = AppStatus.WIP
        mock_app.app_url = None
        mock_app.creator_id = 1
        mock_app.creator = mock_creator
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_app]
        agent_deps.db.execute.return_value = mock_result
        
        ctx = MockRunContext(agent_deps)
        result = await search_apps(ctx, title="Weather")
        
        assert len(result) == 1
        assert result[0]["title"] == "My Weather App"
        assert result[0]["is_mine"] is True  # Same creator
    
    @pytest.mark.asyncio
    async def test_search_returns_empty_list(self, agent_deps):
        """Should return empty list when no matches found."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        agent_deps.db.execute.return_value = mock_result
        
        ctx = MockRunContext(agent_deps)
        result = await search_apps(ctx, url="https://nonexistent.com")
        
        assert result == []


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
