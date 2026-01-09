# Show Your App Backend

The backend for Show Your App, a visual-first aggregation platform for AI-generated software concepts ("Vibe Coding").

## Tech Stack
- **Python**: 3.13
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **Security**: [JWT](https://pyjwt.readthedocs.io/) (via `python-jose`) & `bcrypt`
- **HTTP Client**: [httpx](https://www.python-httpx.org/) for OAuth and external API calls
- **Media**: [S3-Compatible Storage](https://aws.amazon.com/s3/) (AWS, Hetzner, MinIO) for image storage via presigned URLs
- **Observability**: [Logfire](https://logfire.pydantic.dev/) for Pydantic AI agent tracing
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Containerization**: Docker Compose (for local DB)

*   **Framework:** FastAPI
*   **Database:** PostgreSQL
*   **ORM:** SQLAlchemy (Async)
*   **Migrations:** Alembic
*   **Containerization:** Docker & Docker Compose

## Getting Started

### Prerequisites

*   Docker and Docker Compose
*   Python 3.10+ (if running locally without Docker)

### Running with Docker

1.  Make sure you are in the root `vibe_hub` directory (repo name kept for now).
2.  Run `docker-compose up --build`.

The API will be available at `http://localhost:8000`.
API Documentation (Swagger UI) at `http://localhost:8000/docs`.

### Running Tests

To run the tests in a simplified way using `uv`:

```bash
uv run pytest
```

### 4. Environment Configuration
The project uses `.env` files for configuration. Create a `backend/.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/show_your_app
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/show_your_app_test
SECRET_KEY=your_secret_key_here

# S3 / S3-Compatible Storage
S3_BUCKET=your_bucket_name
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_ENDPOINT_URL=https://your-endpoint.com # Optional: for Hetzner, MinIO, etc.

# OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# AI Agent (admin-only feature)
AGENT_API_BASE=https://api.openai.com/v1  # OpenAI-compatible endpoint
AGENT_API_KEY=sk-...                       # API key for the LLM provider
AGENT_MODEL=gpt-4o                         # Model name
AGENT_HEADLESS=true                        # Browser runs headless in production

# Observability (optional)
LOGFIRE_TOKEN=                             # Logfire token for agent tracing
```

### 5. Database Initialization
Run migrations to set up the database schema:
```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/show_your_app
uv run alembic upgrade head
```

### 6. Run Server
```bash
uv run uvicorn app.main:app --reload
```

### 7. Interactive Docs
Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI.

## Testing
The test suite uses a dedicated PostgreSQL test database. The database is automatically created before tests and dropped after completion.

```bash
uv run pytest
```

## Reddit Ingestion

The platform includes a system for ingesting posts from Reddit (r/SideProject) and automatically creating app listings using an AI agent.

### How It Works

1. **Download posts locally** — Fetches Reddit posts from your machine (avoids Reddit's IP blocking of cloud servers)
2. **Submit to production API** — Sends posts to the production server as a background job
3. **Background worker processes** — Server-side worker picks up the job and runs the AI agent for each post
4. **Job tracking** — Monitor progress, view logs, and cancel jobs via API

### Quick Start

```bash
# Full workflow: download + submit to production
./scripts/ingest_reddit_prod.sh --limit 50

# Or step by step:
uv run python scripts/download_reddit_posts.py --limit 50
uv run python scripts/submit_to_prod.py reddit_posts_SideProject_*.ndjson
```

### Configuration

Add these to `.env.production`:

```env
PROD_API_URL=https://your-domain.com/api   # Production API base URL
ADMIN_TOKEN=your_api_key_here              # Admin user's API key (from profile settings)
```

### Available Scripts

| Script | Description |
|--------|-------------|
| `scripts/ingest_reddit_prod.sh` | Full workflow: download locally + submit to prod |
| `scripts/download_reddit_posts.py` | Download Reddit posts to NDJSON file |
| `scripts/submit_to_prod.py` | Submit NDJSON file to production API |

### Script Options

```bash
# ingest_reddit_prod.sh
./scripts/ingest_reddit_prod.sh --limit 50          # Max posts to fetch
./scripts/ingest_reddit_prod.sh --subreddit vibecoding  # Different subreddit
./scripts/ingest_reddit_prod.sh --file posts.ndjson # Skip download, use existing file

# download_reddit_posts.py
uv run python scripts/download_reddit_posts.py --limit 100 --subreddit SideProject --output my_posts.ndjson

# submit_to_prod.py
uv run python scripts/submit_to_prod.py posts.ndjson --api-url https://api.example.com --subreddit SideProject
```

### Job Management API

All endpoints require admin authentication (API key via `X-API-Key` header or JWT via `Authorization: Bearer`).

```bash
# Create job (submit posts for processing)
curl -X POST https://your-domain.com/api/jobs/ingestion \
  -H "X-API-Key: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"posts": [...], "subreddit": "SideProject"}'

# List all jobs
curl https://your-domain.com/api/jobs/ingestion \
  -H "X-API-Key: $ADMIN_TOKEN"

# Get job status and logs
curl https://your-domain.com/api/jobs/ingestion/1 \
  -H "X-API-Key: $ADMIN_TOKEN"

# Cancel a running job
curl -X POST https://your-domain.com/api/jobs/ingestion/1/cancel \
  -H "X-API-Key: $ADMIN_TOKEN"
```

### Job Status Values

| Status | Description |
|--------|-------------|
| `pending` | Job created, waiting for worker to pick up |
| `running` | Worker is processing posts |
| `completed` | All posts processed successfully |
| `failed` | Job encountered a fatal error |
| `cancelled` | Job was cancelled by user |

### Background Worker

The background worker runs automatically when the backend starts:
- Polls for pending jobs every 5 seconds
- Processes posts sequentially through the AI agent
- Updates job progress after each post
- Checks for cancellation between posts
- Auto-deletes jobs older than 30 days

## Project Structure
- `app/`: Main application code.
  - `agent/`: Pydantic AI agent for automated app submission (admin-only).
    - `agent.py`: Agent configuration and runner.
    - `tools.py`: 13 agent tools (DB queries, S3 upload, browser automation).
    - `browser.py`: Playwright browser automation for screenshots.
    - `deps.py`: Dependency injection for agent runs.
  - `core/`: Security, JWT, and centralized configuration (`config.py`).
  - `routers/`: 14 domain-specific API routers (including `media.py`, `agent.py`).
  - `schemas/`: Pydantic models for request/response validation.
  - `models.py`: SQLAlchemy database models.
  - `main.py`: App entry point and router registration.
  - `database.py`: DB engine and session management.
- `tests/`: Integration tests using `TestClient`.
- `migrations/`: Alembic database migration scripts.
- `pyproject.toml`: Project metadata and dependencies.
- `docker-compose.yml`: Local infrastructure (PostgreSQL).
