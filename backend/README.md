# VibeHub Backend

The backend for VibeHub, a visual-first aggregation platform for AI-generated software concepts ("Vibe Coding").

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
- **Testing**: `pytest`

## Core Features
- **Auth**: Secure JWT-based authentication (Stable User IDs) with **Social Login (Google & GitHub)** support.
- **Vibes**: Full lifecycle of AI app concepts (Create, Feed, Fork, Status).
- **Media**: Integrated S3-compatible storage support (AWS, Hetzner, MinIO) using **Presigned URLs** for secure, direct client-side uploads.
- **Social**: Comments, Vibe Checks (0-100% reviews), and Likes.
- **Collaboration**: Implementation submissions and Official status linking.
- **Social Graph**: User following and real-time-like notifications.
- **Content Management**: Dynamic Tools and Tags for masonry feed filtering.

## Getting Started

### 1. Prerequisites
- [uv](https://github.com/astral-sh/uv) installed.
- Docker & Docker Compose installed.

### 2. Infrastructure
Spin up the local PostgreSQL instance:
```bash
docker compose up -d
```

### 3. Setup Project
```bash
uv sync
```

### 4. Environment Configuration
The project uses `.env` files for configuration. Create a `backend/.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/vibehub
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/vibehub_test
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
```

### 5. Database Initialization
Run migrations to set up the database schema:
```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/vibehub
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
  - `core/`: Security, JWT, and centralized configuration (`config.py`).
  - `routers/`: 13 domain-specific API routers (including `media.py`).
  - `schemas/`: Pydantic models for request/response validation.
  - `models.py`: SQLAlchemy database models.
  - `main.py`: App entry point and router registration.
  - `database.py`: DB engine and session management.
- `tests/`: Integration tests using `TestClient`.
- `migrations/`: Alembic database migration scripts.
- `pyproject.toml`: Project metadata and dependencies.
- `docker-compose.yml`: Local infrastructure (PostgreSQL).
