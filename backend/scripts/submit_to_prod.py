#!/usr/bin/env python3
"""
Submit Reddit posts to production server for processing.

This script reads an NDJSON file of Reddit posts and submits them
to the production server's ingestion job API.

Usage:
    cd backend
    uv run python scripts/submit_to_prod.py reddit_posts.ndjson
    uv run python scripts/submit_to_prod.py reddit_posts.ndjson --api-url https://api.showyour.app
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import requests

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_env_file(env_path: Path) -> dict:
    """Load environment variables from a file."""
    env = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env[key] = value
    return env


def main(
    posts_file: str,
    api_url: str = None,
    admin_token: str = None,
    subreddit: str = "SideProject",
):
    """Submit posts to production server."""
    posts_path = Path(posts_file)
    
    if not posts_path.exists():
        logger.error(f"File not found: {posts_path}")
        sys.exit(1)
    
    # Load posts from NDJSON file
    posts = []
    with open(posts_path) as f:
        for line in f:
            line = line.strip()
            if line:
                posts.append(json.loads(line))
    
    logger.info(f"Loaded {len(posts)} posts from {posts_path}")
    
    if not posts:
        logger.warning("No posts to submit")
        return
    
    # Get API URL and admin token
    if not api_url or not admin_token:
        # Try to load from .env.production
        backend_dir = Path(__file__).parent.parent
        env_prod_path = backend_dir.parent / ".env.production"
        env_path = backend_dir / ".env"
        
        env = {}
        if env_prod_path.exists():
            env = load_env_file(env_prod_path)
            logger.info(f"Loaded config from {env_prod_path}")
        elif env_path.exists():
            env = load_env_file(env_path)
            logger.info(f"Loaded config from {env_path}")
        
        if not api_url:
            api_url = env.get("PROD_API_URL", os.environ.get("PROD_API_URL"))
        if not admin_token:
            admin_token = env.get("ADMIN_TOKEN", os.environ.get("ADMIN_TOKEN"))
    
    if not api_url:
        logger.error("API URL not provided. Set PROD_API_URL in .env.production or use --api-url")
        sys.exit(1)
    
    if not admin_token:
        logger.error("Admin token not provided. Set ADMIN_TOKEN in .env.production or use --admin-token")
        sys.exit(1)
    
    # Prepare request
    api_url = api_url.rstrip("/")
    endpoint = f"{api_url}/jobs/ingestion"
    
    # Support both API key and JWT token
    # API keys are shorter, JWT tokens are longer and have dots
    if "." in admin_token and len(admin_token) > 100:
        # Looks like a JWT token
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }
    else:
        # Treat as API key
        headers = {
            "X-API-Key": admin_token,
            "Content-Type": "application/json",
        }
    
    payload = {
        "posts": posts,
        "subreddit": subreddit,
    }
    
    logger.info(f"Submitting {len(posts)} posts to {endpoint}")
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        job_id = result.get("job_id")
        status = result.get("status")
        message = result.get("message")
        
        logger.info("")
        logger.info("=" * 50)
        logger.info("JOB SUBMITTED SUCCESSFULLY")
        logger.info(f"  Job ID: {job_id}")
        logger.info(f"  Status: {status}")
        logger.info(f"  Message: {message}")
        logger.info("")
        logger.info("To check job status:")
        logger.info(f"  curl -H 'Authorization: Bearer $ADMIN_TOKEN' {api_url}/jobs/ingestion/{job_id}")
        logger.info("")
        logger.info("To cancel job:")
        logger.info(f"  curl -X POST -H 'Authorization: Bearer $ADMIN_TOKEN' {api_url}/jobs/ingestion/{job_id}/cancel")
        logger.info("=" * 50)
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                logger.error(f"Response: {e.response.json()}")
            except Exception:
                logger.error(f"Response: {e.response.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit Reddit posts to production server")
    parser.add_argument("posts_file", help="Path to NDJSON file with Reddit posts")
    parser.add_argument("--api-url", type=str, help="Production API URL (default: from PROD_API_URL env)")
    parser.add_argument("--admin-token", type=str, help="Admin JWT token (default: from ADMIN_TOKEN env)")
    parser.add_argument("--subreddit", type=str, default="SideProject", help="Subreddit name (default: SideProject)")
    
    args = parser.parse_args()
    main(
        posts_file=args.posts_file,
        api_url=args.api_url,
        admin_token=args.admin_token,
        subreddit=args.subreddit,
    )
