# Backend Implementation TODOs

Based on the review of `README.md`, `prd.md`, and the codebase, here are the missing pieces required before switching to frontend development.

## 🚨 Critical: Infrastructure & Database
- [x] **Fix Alembic Migrations config**: `migrations/env.py` has `target_metadata = None`. It needs to point to `app.models.Base.metadata` so tables are actually created in Postgres.
- [x] **Dockerize Database**: Create a `docker-compose.yml` file to spin up a local PostgreSQL instance for testing (matching production database type).
- [x] **Verify Migrations**: Run `alembic revision --autogenerate` and `alembic upgrade head` against the local Postgres container.

## 🔐 Authentication (PRD: "Auth: google + github")
- [x] **Add OAuth2 Dependencies**: `httpx` and `authlib` (or manual implementation).
- [x] **Social Login Endpoints**:
    - [x] `POST /auth/google` (Exchange code for token).
    - [x] `POST /auth/github` (Exchange code for token).
- [x] **Update User Model Usage**: Ensure `google_id` and `github_id` are correctly populated during social login.

## 🖼️ Media Handling
- [x] **Image Upload Strategy**:
    - Current implementation expects `image_url` string.
    - [x] **Decision**: Backend handling with Cloudinary.
    - [x] **Implement**: Added `app/routers/media.py` with Cloudinary integration.


## 🚀 Deployment Prep
- [ ] **Seed Data**: Create a script to seed initial Tools (Cursor, Replit, v0) and Tags so the DB isn't empty on first run.
