#!/usr/bin/env python3
"""
Reddit r/SideProject Post Ingestion Script

Fetches posts from r/SideProject, filters for those containing URLs,
checks for duplicates, and runs the agent to evaluate and create app listings.

Usage:
    cd backend
    uv run python scripts/ingest_reddit_posts.py
    uv run python scripts/ingest_reddit_posts.py --limit 10 --dry-run
"""

import argparse
import asyncio
import logging
import re
import sys
import time
from datetime import datetime, timezone

import requests
from sqlalchemy import select, or_

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from app.database import AsyncSessionLocal
from app.models import User, App
from app.agent.agent import run_agent
from app.agent.deps import AgentDeps


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Reddit config
HEADERS = {
    "User-Agent": "SideProjectScraper/1.0 (ShowYourApp ingestion script)"
}
BASE_URL = "https://www.reddit.com"

# URL pattern to extract URLs from post body
URL_PATTERN = re.compile(r'https?://[^\s\)\]\>\"\']+')


def fetch_posts(subreddit: str, sort: str = "new", limit: int = 100, after: str = None) -> tuple[list, str]:
    """Fetch posts from a subreddit using public JSON endpoint."""
    url = f"{BASE_URL}/r/{subreddit}/{sort}.json"
    params = {"limit": min(limit, 100)}
    if after:
        params["after"] = after
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        posts = data.get("data", {}).get("children", [])
        next_after = data.get("data", {}).get("after")
        return [post["data"] for post in posts], next_after
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching posts: {e}")
        return [], None


def fetch_posts_last_48h(subreddit: str, max_posts: int = 100) -> list:
    """Fetch posts from the last 48 hours, sorted by score."""
    cutoff_time = datetime.now(timezone.utc).timestamp() - (48 * 60 * 60)
    all_posts = []
    after = None
    
    while True:
        posts, after = fetch_posts(subreddit, sort="new", limit=100, after=after)
        if not posts:
            break
        
        for post in posts:
            if post["created_utc"] >= cutoff_time:
                all_posts.append(post)
            else:
                all_posts.sort(key=lambda x: x["score"], reverse=True)
                return all_posts[:max_posts]
        
        if not after:
            break
        time.sleep(1)  # Rate limiting
    
    all_posts.sort(key=lambda x: x["score"], reverse=True)
    return all_posts[:max_posts]


def extract_urls(text: str) -> list[str]:
    """Extract all URLs from text."""
    if not text:
        return []
    urls = URL_PATTERN.findall(text)
    # Clean trailing punctuation
    cleaned = []
    for url in urls:
        url = url.rstrip(".,;:!?")
        # Skip Reddit URLs and common non-app URLs
        if "reddit.com" in url or "redd.it" in url:
            continue
        if "imgur.com" in url or "i.redd.it" in url:
            continue
        cleaned.append(url)
    return cleaned


def build_agent_prompt(post: dict) -> str:
    """Build the agent prompt for a Reddit post."""
    title = post.get("title", "")
    selftext = post.get("selftext", "")
    permalink = f"https://reddit.com{post.get('permalink', '')}"
    
    return f"""Evaluate this Reddit post from r/SideProject. 

**Decision criteria:**
- If it showcases a real app or project worth adding to our platform, create an app listing.
- SKIP if it's: spam, a question/discussion, hiring post, self-promotion without an app, or low-quality content.
- If you decide to create an app, use post_url="{permalink}" to track the source.

**Post Title:** {title}

**Post Content:**
{selftext}

If you create an app listing, make sure to:
1. Visit the app URL and take screenshots
2. Check for duplicates first using search_apps
3. Write compelling title, prompt_text, and prd_text
4. Set appropriate tags and tools
"""


async def get_admin_user(db, email: str) -> User:
    """Fetch admin user by email."""
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar()
    if not user:
        raise ValueError(f"Admin user not found: {email}")
    if not user.is_admin:
        raise ValueError(f"User {email} is not an admin")
    return user


async def check_post_processed(db, post_url: str) -> bool:
    """Check if a post has already been processed."""
    result = await db.execute(select(App.id).filter(App.post_url == post_url).limit(1))
    return result.scalar() is not None


async def check_urls_exist(db, urls: list[str]) -> list[str]:
    """Check which URLs already exist as app_url in the database."""
    if not urls:
        return []
    
    # Build OR filter for all URLs (partial match)
    filters = [App.app_url.ilike(f"%{url}%") for url in urls]
    result = await db.execute(select(App.app_url).filter(or_(*filters)))
    existing = result.scalars().all()
    return existing


async def process_post(db, user: User, post: dict, dry_run: bool = False) -> dict:
    """Process a single Reddit post through the agent."""
    title = post.get("title", "Unknown")
    permalink = f"https://reddit.com{post.get('permalink', '')}"
    selftext = post.get("selftext", "")
    
    logger.info(f"Processing: {title[:60]}...")
    
    # Extract URLs from post body
    urls = extract_urls(selftext)
    if not urls:
        logger.info(f"  Skipped: No URLs in post body")
        return {"skipped": True, "reason": "no_urls"}
    
    logger.info(f"  Found {len(urls)} URLs: {urls[:3]}{'...' if len(urls) > 3 else ''}")
    
    # Check if post already processed
    if await check_post_processed(db, permalink):
        logger.info(f"  Skipped: Post already processed")
        return {"skipped": True, "reason": "post_exists"}
    
    # Check if any extracted URL already exists
    existing_urls = await check_urls_exist(db, urls)
    if existing_urls:
        logger.info(f"  Skipped: URL already exists: {existing_urls[0]}")
        return {"skipped": True, "reason": "url_exists", "existing": existing_urls}
    
    if dry_run:
        logger.info(f"  [DRY RUN] Would process with agent")
        return {"dry_run": True, "urls": urls}
    
    # Build prompt and run agent
    prompt = build_agent_prompt(post)
    
    deps = AgentDeps(db=db, user=user)
    result = await run_agent(prompt, deps)
    
    if result.get("success"):
        logger.info(f"  Agent completed. Created apps: {result.get('app_ids', [])}")
    else:
        logger.error(f"  Agent failed: {result.get('error', 'Unknown error')[:100]}")
    
    return result


async def main(limit: int = 50, dry_run: bool = False, subreddit: str = "SideProject"):
    """Main ingestion loop."""
    logger.info(f"Starting Reddit ingestion from r/{subreddit}")
    logger.info(f"Limit: {limit}, Dry run: {dry_run}")
    
    # Fetch posts
    logger.info("Fetching posts from last 48 hours...")
    posts = fetch_posts_last_48h(subreddit, max_posts=limit)
    logger.info(f"Fetched {len(posts)} posts")
    
    if not posts:
        logger.warning("No posts found")
        return
    
    # Filter posts with URLs in body
    posts_with_urls = [p for p in posts if extract_urls(p.get("selftext", ""))]
    logger.info(f"Posts with URLs in body: {len(posts_with_urls)}")
    
    if not posts_with_urls:
        logger.warning("No posts with URLs found")
        return
    
    # Process posts
    stats = {"processed": 0, "created": 0, "skipped": 0, "errors": 0}
    
    async with AsyncSessionLocal() as db:
        # Get admin user
        try:
            admin = await get_admin_user(db, "alexavd@gmail.com")
            logger.info(f"Using admin user: {admin.username} (id={admin.id})")
        except ValueError as e:
            logger.error(str(e))
            return
        
        for i, post in enumerate(posts_with_urls):
            logger.info(f"\n[{i+1}/{len(posts_with_urls)}] Processing post...")
            
            try:
                result = await process_post(db, admin, post, dry_run=dry_run)
                
                if result.get("skipped"):
                    stats["skipped"] += 1
                elif result.get("dry_run"):
                    stats["processed"] += 1
                elif result.get("success"):
                    stats["processed"] += 1
                    stats["created"] += len(result.get("app_ids", []))
                else:
                    stats["errors"] += 1
                    
            except Exception as e:
                logger.exception(f"Error processing post: {e}")
                stats["errors"] += 1
            
            # Rate limiting between agent runs
            if not dry_run and i < len(posts_with_urls) - 1:
                logger.info("  Waiting 2 seconds before next post...")
                await asyncio.sleep(2)
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("INGESTION COMPLETE")
    logger.info(f"  Posts with URLs: {len(posts_with_urls)}")
    logger.info(f"  Processed: {stats['processed']}")
    logger.info(f"  Apps created: {stats['created']}")
    logger.info(f"  Skipped: {stats['skipped']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Reddit r/SideProject posts")
    parser.add_argument("--limit", type=int, default=50, help="Max posts to fetch (default: 50)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be processed without running agent")
    parser.add_argument("--subreddit", type=str, default="SideProject", help="Subreddit to scrape (default: SideProject)")
    
    args = parser.parse_args()
    
    asyncio.run(main(limit=args.limit, dry_run=args.dry_run, subreddit=args.subreddit))
