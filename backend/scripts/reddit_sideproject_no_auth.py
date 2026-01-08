#!/usr/bin/env python3
"""
Reddit SideProject Scraper - No OAuth Required!

This script fetches posts from r/SideProject using Reddit's public JSON endpoints.
NO API KEY OR REGISTRATION NEEDED for read-only public data.

Usage:
    python reddit_sideproject_no_auth.py
"""

import requests
import time
from datetime import datetime, timezone


# Reddit requires a custom User-Agent or it will block requests
HEADERS = {
    "User-Agent": "SideProjectScraper/1.0 (Personal script for monitoring side projects)"
}

BASE_URL = "https://www.reddit.com"


def fetch_posts(subreddit: str, sort: str = "hot", limit: int = 25, time_filter: str = None) -> list:
    """
    Fetch posts from a subreddit using public JSON endpoint.
    
    Args:
        subreddit: Name of the subreddit (without r/)
        sort: Sort method - 'hot', 'new', 'top', 'rising'
        limit: Number of posts to fetch (max 100)
        time_filter: For 'top' sort - 'hour', 'day', 'week', 'month', 'year', 'all'
    
    Returns:
        list: List of post dictionaries
    """
    url = f"{BASE_URL}/r/{subreddit}/{sort}.json"
    
    params = {"limit": min(limit, 100)}
    if time_filter and sort == "top":
        params["t"] = time_filter
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = data.get("data", {}).get("children", [])
        return [post["data"] for post in posts]
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching posts: {e}")
        return []


def fetch_subreddit_info(subreddit: str) -> dict:
    """Fetch subreddit information."""
    url = f"{BASE_URL}/r/{subreddit}/about.json"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("data", {})
    except requests.exceptions.RequestException as e:
        print(f"Error fetching subreddit info: {e}")
        return {}


def format_post(post: dict, index: int) -> str:
    """Format a post for display."""
    created = datetime.fromtimestamp(post["created_utc"], tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    title = post["title"]
    author = post.get("author", "[deleted]")
    
    # Get full post content
    selftext = post.get("selftext", "").strip()
    content = ""
    if selftext:
        # Indent the post content for readability
        indented = "\n".join(f"   {line}" for line in selftext.split('\n'))
        content = f"\n\n   --- Post Content ---\n{indented}\n   --- End ---"
    
    return f"""
{index}. {title}
   Score: {post['score']} | Comments: {post['num_comments']} | Created: {created}
   Author: u/{author}
   URL: {post['url']}
   Reddit: https://reddit.com{post['permalink']}{content}
"""


def main():
    subreddit = "SideProject"
    
    print("=" * 60)
    print(f"Reddit r/{subreddit} Scraper (No Auth Required)")
    print("=" * 60)
    
    # Fetch and display subreddit info
    info = fetch_subreddit_info(subreddit)
    if info:
        print(f"\nSubreddit: r/{info.get('display_name', subreddit)}")
        print(f"Title: {info.get('title', 'N/A')}")
        print(f"Subscribers: {info.get('subscribers', 0):,}")
        print(f"Description: {info.get('public_description', 'N/A')[:200]}...")
    
    # Rate limiting - be nice to Reddit
    time.sleep(1)
    
    # HOT posts
    print("\n" + "=" * 60)
    print("HOT POSTS (Trending)")
    print("=" * 60)
    
    hot_posts = fetch_posts(subreddit, sort="hot", limit=5)
    for i, post in enumerate(hot_posts, 1):
        print(format_post(post, i))
    
    time.sleep(1)  # Rate limiting
    
    # NEW posts
    print("\n" + "=" * 60)
    print("NEW POSTS (Latest)")
    print("=" * 60)
    
    new_posts = fetch_posts(subreddit, sort="new", limit=5)
    for i, post in enumerate(new_posts, 1):
        print(format_post(post, i))
    
    time.sleep(1)  # Rate limiting
    
    # TOP posts this week
    print("\n" + "=" * 60)
    print("TOP POSTS (This Week)")
    print("=" * 60)
    
    top_posts = fetch_posts(subreddit, sort="top", limit=5, time_filter="week")
    for i, post in enumerate(top_posts, 1):
        print(format_post(post, i))
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
