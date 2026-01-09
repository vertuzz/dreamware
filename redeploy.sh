#!/bin/bash
# Quick redeploy script for code changes
set -e

SERVER="root@49.13.204.222"
APP_DIR="/opt/vibe_hub"

# Parse arguments
BACKEND_ONLY=false
FRONTEND_ONLY=false
NO_BUILD=false
NO_CACHE=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--backend) BACKEND_ONLY=true ;;
        -f|--frontend) FRONTEND_ONLY=true ;;
        -q|--quick) NO_BUILD=true ;;
        -c|--no-cache) NO_CACHE=true ;;
        -h|--help) 
            echo "Usage: ./redeploy.sh [options]"
            echo "  -b, --backend   Rebuild backend only"
            echo "  -f, --frontend  Rebuild frontend only"
            echo "  -q, --quick     Restart without rebuilding"
            echo "  -c, --no-cache  Rebuild without Docker cache (for env/config changes)"
            echo "  -h, --help      Show this help"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

echo "=== Redeploying Vibe Hub ==="

# Sync files (excluding local .env files)
echo "Syncing files..."
rsync -az --delete \
    --exclude 'node_modules' --exclude '.venv' --exclude '__pycache__' \
    --exclude '.git' --exclude '*.pyc' --exclude 'backend/.env' --exclude 'frontend/.env' \
    --exclude 'vibe_hub.db' --exclude '.pytest_cache' --exclude 'dist' \
    ./ $SERVER:$APP_DIR/

# Sync .env.production to server's .env (docker-compose uses .env by default)
if [[ -f ".env.production" ]]; then
    echo "Syncing .env.production -> .env on server..."
    rsync -az .env.production $SERVER:$APP_DIR/.env
fi

# Build options
BUILD_OPTS=""
if $NO_CACHE; then
    BUILD_OPTS="--no-cache"
fi

# Rebuild and restart
if $NO_BUILD; then
    echo "Restarting services..."
    ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml restart"
elif $BACKEND_ONLY; then
    echo "Rebuilding backend..."
    ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml build $BUILD_OPTS backend && docker compose -f docker-compose.prod.yml up -d backend"
elif $FRONTEND_ONLY; then
    echo "Rebuilding frontend..."
    ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml build $BUILD_OPTS frontend && docker compose -f docker-compose.prod.yml up -d frontend && docker compose -f docker-compose.prod.yml restart nginx"
else
    echo "Rebuilding all services..."
    ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml build $BUILD_OPTS && docker compose -f docker-compose.prod.yml up -d"
fi

# Clean up old/dangling images to prevent disk bloat
echo "Cleaning up unused images..."
ssh $SERVER "docker image prune -f && docker builder prune -f --keep-storage=2GB"

# Show status
echo ""
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml ps"

echo ""
echo "=== Redeploy complete! ==="
echo "https://show-your.app"
