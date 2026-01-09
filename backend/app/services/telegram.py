"""
Telegram admin notification service.

Fire-and-forget notifications for admin tracking of user actions.
Uses asyncio.create_task() to avoid blocking the main request.
Includes simple rate limiting to avoid hitting Telegram API limits.
"""

import asyncio
import time
from collections import deque
from typing import Optional

import httpx

from app.core.config import settings

# Simple rate limiter: max 20 messages per 60 seconds
_message_timestamps: deque[float] = deque(maxlen=20)
_RATE_LIMIT_WINDOW = 60.0  # seconds
_RATE_LIMIT_MAX = 20  # max messages per window


def _is_rate_limited() -> bool:
    """Check if we've exceeded the rate limit."""
    now = time.time()
    # Remove timestamps older than the window
    while _message_timestamps and now - _message_timestamps[0] > _RATE_LIMIT_WINDOW:
        _message_timestamps.popleft()
    return len(_message_timestamps) >= _RATE_LIMIT_MAX


def _record_message() -> None:
    """Record a message timestamp for rate limiting."""
    _message_timestamps.append(time.time())


async def _send_telegram_message(message: str) -> None:
    """
    Send a message to Telegram. Internal function - do not call directly.
    Use the notify_* helpers which spawn fire-and-forget tasks.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return  # Silently skip if not configured
    
    if _is_rate_limited():
        return  # Drop message if rate limited
    
    _record_message()
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            })
    except Exception:
        pass  # Fire-and-forget - don't fail the main request


def _escape_html(text: str | None) -> str:
    """Escape HTML special characters for Telegram."""
    if text is None:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --- Public notification helpers ---
# Each spawns a fire-and-forget task via asyncio.create_task()

def notify_new_user(username: str, provider: str) -> None:
    """Notify admin of new user registration."""
    message = f"👤 New user: <b>{_escape_html(username)}</b> via {_escape_html(provider)}"
    asyncio.create_task(_send_telegram_message(message))


def notify_app_created(username: str, app_title: str, app_slug: str) -> None:
    """Notify admin of new app creation."""
    message = f"🚀 New app: <b>{_escape_html(app_title)}</b> by {_escape_html(username)}"
    asyncio.create_task(_send_telegram_message(message))


def notify_like(username: str, app_title: str) -> None:
    """Notify admin of app like."""
    message = f"👍 <b>{_escape_html(username)}</b> liked <b>{_escape_html(app_title)}</b>"
    asyncio.create_task(_send_telegram_message(message))


def notify_comment(username: str, app_title: str, comment_preview: str) -> None:
    """Notify admin of new comment."""
    # Truncate comment to ~50 chars
    preview = comment_preview[:50] + "..." if len(comment_preview) > 50 else comment_preview
    message = f"💬 <b>{_escape_html(username)}</b> commented on <b>{_escape_html(app_title)}</b>: {_escape_html(preview)}"
    asyncio.create_task(_send_telegram_message(message))


def notify_ownership_claim(username: str, app_title: str) -> None:
    """Notify admin of ownership claim."""
    message = f"🔑 <b>{_escape_html(username)}</b> claimed ownership of <b>{_escape_html(app_title)}</b>"
    asyncio.create_task(_send_telegram_message(message))


def notify_feedback(username: str, feedback_type: str, message_preview: str) -> None:
    """Notify admin of feedback submission."""
    preview = message_preview[:50] + "..." if len(message_preview) > 50 else message_preview
    message = f"📝 Feedback ({_escape_html(feedback_type)}) from <b>{_escape_html(username)}</b>: {_escape_html(preview)}"
    asyncio.create_task(_send_telegram_message(message))
