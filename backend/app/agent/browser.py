"""Browser automation utilities using Playwright for the agent."""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page


class BrowserManager:
    """Manages Playwright browser instance for agent automation."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._screenshot_dir = Path(tempfile.mkdtemp(prefix="agent_screenshots_"))
    
    async def start(self) -> None:
        """Initialize browser if not already running."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._page = await self._browser.new_page()
    
    async def stop(self) -> None:
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    async def navigate(self, url: str, timeout: int = 30000) -> dict:
        """Navigate to a URL and wait for load.
        
        Returns:
            Dict with status and page title.
        """
        await self.start()
        try:
            await self._page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            title = await self._page.title()
            return {
                "success": True,
                "url": self._page.url,
                "title": title,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def take_screenshot(self, name: str = "screenshot") -> dict:
        """Take a screenshot of the current page.
        
        Returns:
            Dict with file path and success status.
        """
        if not self._page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            # Ensure name is safe for filesystem
            safe_name = "".join(c for c in name if c.isalnum() or c in "._-")
            if not safe_name:
                safe_name = "screenshot"
            
            file_path = self._screenshot_dir / f"{safe_name}.png"
            await self._page.screenshot(path=str(file_path), full_page=False)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "size_bytes": file_path.stat().st_size,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_page_content(self) -> dict:
        """Get the text content of the current page.
        
        Returns:
            Dict with page content and metadata.
        """
        if not self._page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            # Get visible text content
            content = await self._page.evaluate("""
                () => {
                    // Get main content areas
                    const selectors = ['main', 'article', '[role="main"]', '.content', '#content', 'body'];
                    for (const selector of selectors) {
                        const el = document.querySelector(selector);
                        if (el) {
                            return el.innerText.slice(0, 10000);  // Limit to 10k chars
                        }
                    }
                    return document.body.innerText.slice(0, 10000);
                }
            """)
            
            title = await self._page.title()
            url = self._page.url
            
            return {
                "success": True,
                "title": title,
                "url": url,
                "content": content,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def click(self, selector: str) -> dict:
        """Click an element on the page.
        
        Args:
            selector: CSS selector for the element to click.
            
        Returns:
            Dict with success status.
        """
        if not self._page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            await self._page.click(selector, timeout=5000)
            await asyncio.sleep(0.5)  # Wait for any animations
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def scroll(self, direction: str = "down", amount: int = 500) -> dict:
        """Scroll the page.
        
        Args:
            direction: "up" or "down"
            amount: Pixels to scroll
            
        Returns:
            Dict with success status.
        """
        if not self._page:
            return {"success": False, "error": "Browser not started"}
        
        try:
            delta = amount if direction == "down" else -amount
            await self._page.mouse.wheel(0, delta)
            await asyncio.sleep(0.3)
            return {"success": True, "direction": direction, "amount": amount}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_screenshot_path(self, name: str) -> Path:
        """Get the path where a screenshot would be saved."""
        safe_name = "".join(c for c in name if c.isalnum() or c in "._-") or "screenshot"
        return self._screenshot_dir / f"{safe_name}.png"


# Global browser manager instance (created per agent run)
_browser_manager: Optional[BrowserManager] = None


async def get_browser(headless: bool = True) -> BrowserManager:
    """Get or create a browser manager instance."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager(headless=headless)
    return _browser_manager


async def cleanup_browser() -> None:
    """Cleanup the global browser instance."""
    global _browser_manager
    if _browser_manager:
        await _browser_manager.stop()
        _browser_manager = None
