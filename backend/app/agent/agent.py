"""Pydantic AI Agent for submitting apps to Show Your App."""

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.agent.deps import AgentDeps
from app.agent.tools import ALL_TOOLS
from app.agent.browser import cleanup_browser
from app.core.config import settings


SYSTEM_PROMPT = """# Show Your App - Agent Instructions

## Purpose
Show Your App is a launchpad for AI-generated software. Your job is to submit a polished listing so humans can discover, try, and give feedback on the app.

**Goal:** Create a compelling showcase that makes users want to click "Try It Now".

## Input You Will Receive
You will be provided with text—most likely a post from Reddit or another site—that describes an app. This post will typically include:
- A description or discussion about the app
- **A link to the live app or demo**

## Your Task (Before Submitting)

### 1. Visit the App Link
If the post contains a link to the app:
1. **Navigate to the URL** using browser_navigate
2. **Explore the app** — Use browser_click to interact, understand what it does
3. **Take screenshots** using browser_screenshot — Capture the main UI, key features
4. **Read the page content** using browser_get_content to understand the value

### 2. Gather Information
From both the post and your exploration, collect:
- App name/title
- What the app does (for prompt_text and prd_text)
- Key features
- Tech stack / tools used (if mentioned)
- Relevant categories/tags
- The live URL

### 3. Check for Duplicates
Use get_my_apps to check if this app already exists. If so, use update_app instead.

### 4. Submit to Show Your App
Use create_app to create the listing with:
- A descriptive title (not generic like "My App")
- A compelling 1-2 sentence hook (prompt_text)
- Full HTML description (prd_text) with <h2>, <p>, <ul>, <li> tags
- Appropriate tool_ids and tag_ids
- The app_url if it's live

### 5. Upload Screenshots
For each screenshot:
1. Get upload URL with get_presigned_url
2. Upload with upload_file_to_s3
3. Attach to app with attach_media_to_app

## Field Requirements

| Field | Required | Purpose |
|-------|----------|---------|
| title | Yes | App name. Be specific, not generic. |
| prompt_text | Yes | 1-2 sentence hook. Sells the app. |
| prd_text | Yes | Full description in HTML format. |
| status | Yes | "Live" if deployed, "WIP" if in progress, "Concept" if idea only. |
| tool_ids | Recommended | IDs from get_available_tools. Pick 1-3. |
| tag_ids | Recommended | IDs from get_available_tags. Pick 4-6. |
| app_url | Required if Live | Link to working app. |

## Writing Quality Content

### title — Be descriptive
- ❌ Bad: "My App", "Cool Tool", "Test"
- ✅ Good: "PixelPet - Virtual AI Companion", "QuickInvoice - Invoice Generator"

### prompt_text — The hook users see first
- ❌ Bad: "An app I made"
- ✅ Good: "Generate professional invoices in 30 seconds with AI-powered auto-fill"

### prd_text — HTML description
```html
<h2>What It Does</h2>
<p>Clear explanation of the app's purpose and main features.</p>

<h2>Key Features</h2>
<ul>
  <li><strong>Feature 1:</strong> Description</li>
  <li><strong>Feature 2:</strong> Description</li>
</ul>

<h2>How It Was Built</h2>
<p>Brief story: what tools were used, any interesting details.</p>
```

## Common Mistakes to Avoid
- Not visiting the app link first
- Generic titles like "Test App"
- Empty or vague prompt_text
- Using Markdown in prd_text (use HTML!)
- No screenshots (always take 2-4)
- Wrong status (use "Live" only if app_url works)
"""


def _create_agent() -> Agent[AgentDeps, str]:
    """Create and configure the Pydantic AI agent."""
    
    # Configure model based on settings
    if settings.AGENT_API_BASE and settings.AGENT_API_KEY:
        provider = OpenAIProvider(
            base_url=settings.AGENT_API_BASE,
            api_key=settings.AGENT_API_KEY,
        )
        model = OpenAIModel(settings.AGENT_MODEL, provider=provider)
    else:
        # Fall back to default OpenAI (requires OPENAI_API_KEY env var)
        model = OpenAIModel(settings.AGENT_MODEL)
    
    agent = Agent(
        model,
        deps_type=AgentDeps,
        system_prompt=SYSTEM_PROMPT,
    )
    
    # Register all tools
    for tool_func in ALL_TOOLS:
        agent.tool(tool_func)
    
    return agent


# Create singleton agent instance
_agent: Agent[AgentDeps, str] | None = None


def get_agent() -> Agent[AgentDeps, str]:
    """Get or create the agent instance."""
    global _agent
    if _agent is None:
        _agent = _create_agent()
    return _agent


async def run_agent(prompt: str, deps: AgentDeps) -> dict:
    """Run the agent with a user prompt.
    
    Args:
        prompt: The user's input (e.g., Reddit post with app link)
        deps: Agent dependencies with DB session and user context
        
    Returns:
        Dict with result text and created app IDs.
    """
    import traceback
    import logging
    
    logger = logging.getLogger(__name__)
    agent = get_agent()
    
    try:
        logger.info(f"Starting agent run for user {deps.user.id}")
        result = await agent.run(prompt, deps=deps)
        
        # Commit any database changes
        await deps.db.commit()
        
        logger.info(f"Agent run completed. Created apps: {deps.created_app_ids}")
        
        return {
            "success": True,
            "result": result.output,  # pydantic-ai uses .output not .data
            "app_ids": deps.created_app_ids,
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Agent run failed: {e}\n{error_trace}")
        await deps.db.rollback()
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}\n\nTraceback:\n{error_trace}",
            "app_ids": [],
        }
    finally:
        # Cleanup browser
        await cleanup_browser()
