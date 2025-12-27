import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.core.config import settings

@pytest.fixture(autouse=True)
def mock_oauth_settings():
    with patch.object(settings, "GOOGLE_CLIENT_ID", "google-id"), \
         patch.object(settings, "GOOGLE_CLIENT_SECRET", "google-secret"), \
         patch.object(settings, "GITHUB_CLIENT_ID", "github-id"), \
         patch.object(settings, "GITHUB_CLIENT_SECRET", "github-secret"):
        yield

@pytest.mark.asyncio
async def test_google_login_new_user(client: TestClient):
    # Mock Google token exchange
    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "google-access-token"}
    
    # Mock Google user info
    mock_user_info_response = MagicMock()
    mock_user_info_response.status_code = 200
    mock_user_info_response.json.return_value = {
        "email": "google@example.com",
        "sub": "google-sub-123",
        "picture": "http://avatar.com/google",
        "name": "Google User"
    }

    with patch("httpx.AsyncClient.post", return_value=mock_token_response), \
         patch("httpx.AsyncClient.get", return_value=mock_user_info_response):
        
        response = client.post("/auth/google", json={"code": "some-google-code"})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_github_login_new_user(client: TestClient):
    # Mock GitHub token exchange
    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "github-access-token"}
    
    # Mock GitHub user info
    mock_user_info_response = MagicMock()
    mock_user_info_response.status_code = 200
    mock_user_info_response.json.return_value = {
        "id": 12345,
        "login": "githubuser",
        "avatar_url": "http://avatar.com/github",
        "email": "github@example.com"
    }

    with patch("httpx.AsyncClient.post", return_value=mock_token_response), \
         patch("httpx.AsyncClient.get", return_value=mock_user_info_response):
        
        response = client.post("/auth/github", json={"code": "some-github-code"})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_google_login_existing_user_by_email(client: TestClient):
    # Register user first
    client.post("/auth/register", json={
        "username": "existinguser",
        "email": "google@example.com",
        "password": "password123"
    })

    # Mock Google token exchange
    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "google-access-token"}
    
    # Mock Google user info
    mock_user_info_response = MagicMock()
    mock_user_info_response.status_code = 200
    mock_user_info_response.json.return_value = {
        "email": "google@example.com",
        "sub": "google-sub-123",
        "picture": "http://avatar.com/google",
        "name": "Google User"
    }

    with patch("httpx.AsyncClient.post", return_value=mock_token_response), \
         patch("httpx.AsyncClient.get", return_value=mock_user_info_response):
        
        response = client.post("/auth/google", json={"code": "some-google-code"})
        
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_github_login_private_email(client: TestClient):
    # Mock GitHub token exchange
    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "github-access-token"}
    
    # Mock GitHub user info (no email)
    mock_user_info_response = MagicMock()
    mock_user_info_response.status_code = 200
    mock_user_info_response.json.return_value = {
        "id": 12345,
        "login": "githubuser",
        "avatar_url": "http://avatar.com/github",
        "email": None
    }

    # Mock GitHub emails
    mock_emails_response = MagicMock()
    mock_emails_response.status_code = 200
    mock_emails_response.json.return_value = [
        {"email": "private@example.com", "primary": True, "verified": True}
    ]

    with patch("httpx.AsyncClient.post", return_value=mock_token_response), \
         patch("httpx.AsyncClient.get") as mock_get:
        
        mock_get.side_effect = [mock_user_info_response, mock_emails_response]
        
        response = client.post("/auth/github", json={"code": "some-github-code"})
        
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_google_login_missing_config(client: TestClient):
    with patch.object(settings, "GOOGLE_CLIENT_ID", None):
        response = client.post("/auth/google", json={"code": "some-code"})
        assert response.status_code == 500
        assert "Google OAuth not configured" in response.json()["detail"]

@pytest.mark.asyncio
async def test_google_login_exchange_fail(client: TestClient):
    mock_token_response = MagicMock()
    mock_token_response.status_code = 400
    mock_token_response.text = "invalid code"
    
    with patch("httpx.AsyncClient.post", return_value=mock_token_response):
        response = client.post("/auth/google", json={"code": "bad-code"})
        assert response.status_code == 400
        assert "Failed to exchange Google code" in response.json()["detail"]

@pytest.mark.asyncio
async def test_github_login_no_email_fail(client: TestClient):
    # Mock GitHub token exchange
    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "github-access-token"}
    
    # Mock GitHub user info (no email)
    mock_user_info_response = MagicMock()
    mock_user_info_response.status_code = 200
    mock_user_info_response.json.return_value = {
        "id": 12345,
        "login": "githubuser",
        "avatar_url": "http://avatar.com/github",
        "email": None
    }

    # Mock GitHub emails fail
    mock_emails_response = MagicMock()
    mock_emails_response.status_code = 400

    with patch("httpx.AsyncClient.post", return_value=mock_token_response), \
         patch("httpx.AsyncClient.get") as mock_get:
        
        mock_get.side_effect = [mock_user_info_response, mock_emails_response]
        
        response = client.post("/auth/github", json={"code": "some-github-code"})
        
        assert response.status_code == 400
        assert "Failed to get GitHub user email" in response.json()["detail"]

@pytest.mark.asyncio
async def test_google_login_username_collision(client: TestClient):
    # Register user with the same base username
    client.post("/auth/register", json={
        "username": "googleuser",
        "email": "other@example.com",
        "password": "password123"
    })

    # Mock Google token exchange
    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "google-access-token"}
    
    # Mock Google user info
    mock_user_info_response = MagicMock()
    mock_user_info_response.status_code = 200
    mock_user_info_response.json.return_value = {
        "email": "google@example.com",
        "sub": "google-sub-123",
        "picture": "http://avatar.com/google",
        "name": "Google User"
    }

    with patch("httpx.AsyncClient.post", return_value=mock_token_response), \
         patch("httpx.AsyncClient.get", return_value=mock_user_info_response):
        
        response = client.post("/auth/google", json={"code": "some-google-code"})
        
        assert response.status_code == 200
        # The username should be "googleuser1" now
        # We can't easily check the DB here without a session, but we can check if it succeeded
        assert "access_token" in response.json()
