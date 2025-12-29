import pytest
from httpx import AsyncClient
from app.models import User, DreamStatus
from sqlalchemy import select

@pytest.mark.asyncio
async def test_api_key_auth_and_dream_v2_fields(client: AsyncClient, db_session):
    # 1. Create a user with an API key
    user = User(
        username="agent_user",
        email="agent@example.com",
        hashed_password="hashed_password",
        api_key="secret-agent-key",
        reputation_score=0.0
    )
    db_session.add(user)
    await db_session.commit()
    
    # 2. Try to create a dream using X-API-Key header
    dream_data = {
        "prompt_text": "A futuristic city built on clouds",
        "prd_text": "Full specs for cloud city",
        "status": "Live",
        "app_url": "https://cloud-city.vercel.app",
        "is_agent_submitted": True,
        "tool_ids": [],
        "tag_ids": []
    }
    
    response = await client.post(
        "/dreams/",
        json=dream_data,
        headers={"X-API-Key": "secret-agent-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["app_url"] == "https://cloud-city.vercel.app"
    assert data["is_agent_submitted"] is True
    assert data["creator_id"] == user.id

@pytest.mark.asyncio
async def test_api_key_auth_failure(client: AsyncClient):
    response = await client.post(
        "/dreams/",
        json={"prompt_text": "test"},
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401
@pytest.mark.asyncio
async def test_dream_with_title_and_no_prompt(client: AsyncClient, auth_headers: dict):
    dream_data = {
        "title": "My Dream Title",
        "prompt_text": None,
        "status": "Concept"
    }
    response = await client.post(
        "/dreams/",
        json=dream_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "My Dream Title"
    assert data["prompt_text"] is None
