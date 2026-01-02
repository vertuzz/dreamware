import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_follow_notification(client: AsyncClient):
    # Register User 1
    u1_data = {"username": "notif_u1", "email": "notif_u1@e.com", "password": "pw"}
    await client.post("/auth/register", json=u1_data)
    login1 = await client.post("/auth/login", data={"username": "notif_u1", "password": "pw"})
    token1 = login1.json()["access_token"]
    
    # Register User 2
    u2_data = {"username": "notif_u2", "email": "notif_u2@e.com", "password": "pw"}
    await client.post("/auth/register", json=u2_data)
    login2 = await client.post("/auth/login", data={"username": "notif_u2", "password": "pw"})
    token2 = login2.json()["access_token"]
    
    # Get User 2 ID
    me2 = await client.get("/auth/me", headers={"Authorization": f"Bearer {token2}"})
    id2 = me2.json()["id"]

    # User 1 follows User 2
    response = await client.post(
        f"/users/{id2}/follow",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200

    # User 2 checks notifications
    response = await client.get(
        "/notifications/",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) > 0
    assert notifications[0]["content"] == "notif_u1 followed you"
    assert notifications[0]["type"] == "follow"

    # Mark as read
    notif_id = notifications[0]["id"]
    response = await client.patch(
        f"/notifications/{notif_id}/read",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 200
    assert response.json()["is_read"] == True
