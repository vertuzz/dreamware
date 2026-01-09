#!/bin/bash
# Download Reddit posts locally and submit to production server for processing
# This avoids Reddit's IP blocking of cloud servers by fetching locally
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
LIMIT=50
SUBREDDIT="SideProject"
POSTS_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --subreddit)
            SUBREDDIT="$2"
            shift 2
            ;;
        --file)
            POSTS_FILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--limit N] [--subreddit NAME] [--file posts.ndjson]"
            echo ""
            echo "Options:"
            echo "  --limit N          Max posts to fetch (default: 50)"
            echo "  --subreddit NAME   Subreddit to scrape (default: SideProject)"
            echo "  --file FILE        Skip download, use existing NDJSON file"
            exit 1
            ;;
    esac
done

echo "=== Reddit Ingestion (Local Download -> Prod API) ==="
echo ""

# Load production config
if [ -f "$BACKEND_DIR/../.env.production" ]; then
    export PROD_API_URL=$(grep "^PROD_API_URL=" "$BACKEND_DIR/../.env.production" | cut -d'=' -f2-)
    export ADMIN_TOKEN=$(grep "^ADMIN_TOKEN=" "$BACKEND_DIR/../.env.production" | cut -d'=' -f2-)
    
    if [ -z "$PROD_API_URL" ]; then
        echo "ERROR: PROD_API_URL not found in .env.production"
        exit 1
    fi
    if [ -z "$ADMIN_TOKEN" ]; then
        echo "ERROR: ADMIN_TOKEN not found in .env.production"
        exit 1
    fi
    
    echo "Loaded config from .env.production"
    echo "API URL: $PROD_API_URL"
else
    echo "ERROR: .env.production not found"
    exit 1
fi

cd "$BACKEND_DIR"

# Step 1: Download posts (or use provided file)
if [ -z "$POSTS_FILE" ]; then
    echo ""
    echo "Step 1: Downloading posts from r/$SUBREDDIT..."
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    POSTS_FILE="reddit_posts_${SUBREDDIT}_${TIMESTAMP}.ndjson"
    
    uv run python scripts/download_reddit_posts.py \
        --limit "$LIMIT" \
        --subreddit "$SUBREDDIT" \
        --output "$POSTS_FILE"
    
    if [ ! -f "$POSTS_FILE" ]; then
        echo "ERROR: Download failed, no output file created"
        exit 1
    fi
else
    echo ""
    echo "Step 1: Using existing file: $POSTS_FILE"
    if [ ! -f "$POSTS_FILE" ]; then
        echo "ERROR: File not found: $POSTS_FILE"
        exit 1
    fi
fi

# Count posts
POST_COUNT=$(wc -l < "$POSTS_FILE")
echo "Posts to submit: $POST_COUNT"

if [ "$POST_COUNT" -eq 0 ]; then
    echo "No posts to submit"
    exit 0
fi

# Step 2: Submit to production
echo ""
echo "Step 2: Submitting to production server..."
uv run python scripts/submit_to_prod.py "$POSTS_FILE" --subreddit "$SUBREDDIT"

echo ""
echo "=== Done ==="
echo "Posts file saved: $POSTS_FILE"
