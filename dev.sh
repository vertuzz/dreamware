#!/bin/bash

# Configuration
DB_CONTAINER_NAME="dreamware-db"
DB_USER="user"
DB_NAME="dreamware"

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local pid=$(lsof -t -i :$port)
    if [ ! -z "$pid" ]; then
        echo "🔪 Killing existing process on port $port (PID: $pid)..."
        kill -9 $pid 2>/dev/null
    fi
}

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "🚀 Shutting down services..."
    # Kill background jobs
    kill $(jobs -p) 2>/dev/null
    # Ensure ports are cleared
    kill_port 8000
    kill_port 5173
    exit
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo "🧹 Cleaning up existing processes..."
kill_port 8000
kill_port 5173

echo "🐳 Starting Docker database..."
docker compose up -d db

echo "⏳ Waiting for database to be ready..."
# Wait for postgres to be ready
MAX_RETRIES=30
RETRY_COUNT=0
until docker exec $DB_CONTAINER_NAME pg_isready -U $DB_USER -d $DB_NAME > /dev/null 2>&1 || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
  echo "   - Database is unavailable - sleeping ($RETRY_COUNT/$MAX_RETRIES)"
  sleep 1
  ((RETRY_COUNT++))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Database failed to start in time. Exiting."
    exit 1
fi

echo "✅ Database is up!"

echo "🔄 Running backend migrations..."
(cd backend && uv run alembic upgrade head)

echo "🔥 Starting Backend..."
(cd backend && uv run uvicorn app.main:app --reload) &

echo "✨ Starting Frontend..."
(cd frontend && pnpm dev) &

echo "---------------------------------------------------"
echo "All services are starting up!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173 (Check terminal output for exact port)"
echo "Press Ctrl+C to stop all services."
echo "---------------------------------------------------"

# Wait for all background processes
wait
