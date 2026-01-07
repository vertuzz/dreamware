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
