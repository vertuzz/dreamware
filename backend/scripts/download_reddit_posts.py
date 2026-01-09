#!/usr/bin/env python3
"""
Download Reddit posts and save to NDJSON file.

This script fetches posts from a subreddit, filters for those with URLs,
and saves them to a file for later submission to the production server.

Usage:
    cd backend
    uv run python scripts/download_reddit_posts.py
    uv run python scripts/download_reddit_posts.py --limit 100 --subreddit SideProject
    uv run python scripts/download_reddit_posts.py --output posts.ndjson
"""

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

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


def main(limit: int = 50, subreddit: str = "SideProject", output: str = None):
    """Download Reddit posts and save to NDJSON file."""
    logger.info(f"Fetching posts from r/{subreddit}")
    logger.info(f"Limit: {limit}")
    
    # Fetch posts
    logger.info("Fetching posts from last 48 hours...")
    posts = fetch_posts_last_48h(subreddit, max_posts=limit)
    logger.info(f"Fetched {len(posts)} posts")
    
    if not posts:
        logger.warning("No posts found")
        return
    
    # Filter posts with URLs in body
    posts_with_urls = []
    for post in posts:
        selftext = post.get("selftext", "")
        urls = extract_urls(selftext)
        if urls:
            posts_with_urls.append({
                "title": post.get("title", ""),
                "selftext": selftext,
                "permalink": post.get("permalink", ""),
                "score": post.get("score", 0),
                "created_utc": post.get("created_utc", 0),
                "extracted_urls": urls,
            })
    
    logger.info(f"Posts with URLs in body: {len(posts_with_urls)}")
    
    if not posts_with_urls:
        logger.warning("No posts with URLs found")
        return
    
    # Determine output filename
    if output:
        output_path = Path(output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"reddit_posts_{subreddit}_{timestamp}.ndjson")
    
    # Write to NDJSON file
    with open(output_path, "w") as f:
        for post in posts_with_urls:
            f.write(json.dumps(post) + "\n")
    
    logger.info(f"Saved {len(posts_with_urls)} posts to {output_path}")
    logger.info("")
    logger.info("To submit to production server:")
    logger.info(f"  uv run python scripts/submit_to_prod.py {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Reddit posts to NDJSON file")
    parser.add_argument("--limit", type=int, default=50, help="Max posts to fetch (default: 50)")
    parser.add_argument("--subreddit", type=str, default="SideProject", help="Subreddit to scrape (default: SideProject)")
    parser.add_argument("--output", "-o", type=str, help="Output filename (default: reddit_posts_<subreddit>_<timestamp>.ndjson)")
    
    args = parser.parse_args()
    main(limit=args.limit, subreddit=args.subreddit, output=args.output)
