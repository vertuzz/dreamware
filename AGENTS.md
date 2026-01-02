# AGENTS.md: System Instructions for Dreamware

## Objective
Dreamware is a launchpad and showcase platform for AI-generated software ("Vibe Coding"). Your goal as an AI agent is to help creators ship their apps, get feedback, and manage their "Dreams" autonomously.

## Environment Setup
### Backend
The backend uses **Python 3.13** and **uv**.
```bash
cd backend
uv run uvicorn app.main:app --reload
```
API: `http://localhost:8000` | Docs: `/docs`

### Frontend
The frontend uses **React (Vite)** and **Tailwind CSS v4**.
```bash
cd frontend
npm install
npm run dev
```
URL: `http://localhost:5173`


### Running Tests
```bash
cd backend
uv run pytest
```

## Authentication
Agents interact with the API using an **API Key**.
- Header: `X-API-Key: <your_api_key>`
- Users can find or regenerate their API key in their profile/settings.
