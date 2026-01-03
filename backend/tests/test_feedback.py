import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_feedback_requires_auth(client: AsyncClient):
    """Test that feedback submission requires authentication."""
    resp = await client.post("/feedback/", json={"type": "feature", "message": "Great app!"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_feedback_success(client: AsyncClient, auth_headers: dict):
    """Test that authenticated users can submit feedback."""
    resp = await client.post(
        "/feedback/",
        json={"type": "feature", "message": "Add dark mode please!"},
        headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] is not None
    assert data["type"] == "feature"
    assert data["message"] == "Add dark mode please!"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_feedback_bug_type(client: AsyncClient, auth_headers: dict):
    """Test creating feedback with bug type."""
    resp = await client.post(
        "/feedback/",
        json={"type": "bug", "message": "Button not working"},
        headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["type"] == "bug"


@pytest.mark.asyncio
async def test_create_feedback_other_type(client: AsyncClient, auth_headers: dict):
    """Test creating feedback with 'other' type."""
    resp = await client.post(
        "/feedback/",
        json={"type": "other", "message": "Just wanted to say hi"},
        headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["type"] == "other"


@pytest.mark.asyncio
async def test_list_feedback_requires_admin(client: AsyncClient, auth_headers: dict):
    """Test that listing feedback requires admin access."""
    resp = await client.get("/feedback/", headers=auth_headers)
    assert resp.status_code == 403
    assert "Admin access required" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_list_feedback_admin_success(client: AsyncClient, auth_headers: dict, admin_headers: dict):
    """Test that admins can list all feedback."""
    # Create some feedback as regular user
    await client.post(
        "/feedback/",
        json={"type": "feature", "message": "Feature request 1"},
        headers=auth_headers
    )
    await client.post(
        "/feedback/",
        json={"type": "bug", "message": "Bug report 1"},
        headers=auth_headers
    )
    
    # List as admin
    resp = await client.get("/feedback/", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    # Should be ordered by created_at desc
    assert data[0]["message"] == "Bug report 1"
    assert data[1]["message"] == "Feature request 1"


@pytest.mark.asyncio
async def test_list_feedback_includes_user_info(client: AsyncClient, auth_headers: dict, admin_headers: dict):
    """Test that feedback list includes user information."""
    await client.post(
        "/feedback/",
        json={"type": "feature", "message": "Test with user info"},
        headers=auth_headers
    )
    
    resp = await client.get("/feedback/", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["user"] is not None
    assert data[0]["user"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_delete_feedback_requires_admin(client: AsyncClient, auth_headers: dict):
    """Test that deleting feedback requires admin access."""
    # Create feedback
    resp = await client.post(
        "/feedback/",
        json={"type": "feature", "message": "To be deleted"},
        headers=auth_headers
    )
    feedback_id = resp.json()["id"]
    
    # Try to delete as regular user
    resp = await client.delete(f"/feedback/{feedback_id}", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_feedback_admin_success(client: AsyncClient, auth_headers: dict, admin_headers: dict):
    """Test that admins can delete feedback."""
    # Create feedback
    resp = await client.post(
        "/feedback/",
        json={"type": "feature", "message": "To be deleted by admin"},
        headers=auth_headers
    )
    feedback_id = resp.json()["id"]
    
    # Delete as admin
    resp = await client.delete(f"/feedback/{feedback_id}", headers=admin_headers)
    assert resp.status_code == 204
    
    # Verify it's deleted
    resp = await client.get("/feedback/", headers=admin_headers)
    feedback_ids = [f["id"] for f in resp.json()]
    assert feedback_id not in feedback_ids


@pytest.mark.asyncio
async def test_delete_feedback_not_found(client: AsyncClient, admin_headers: dict):
    """Test deleting non-existent feedback returns 404."""
    resp = await client.delete("/feedback/99999", headers=admin_headers)
    assert resp.status_code == 404
