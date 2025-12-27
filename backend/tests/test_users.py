import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_user_profile_and_links(client: AsyncClient, auth_headers: dict):
    # 1. Get Me
    me_resp = await client.get("/auth/me", headers=auth_headers)
    user_id = me_resp.json()["id"]
    
    # 2. Update profile
    update_data = {"username": "updated_name", "avatar": "http://new-avatar.png"}
    patch_resp = await client.patch(f"/users/{user_id}", json=update_data, headers=auth_headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["username"] == "updated_name"
    
    # 3. Add Link
    link_data = {"label": "GitHub", "url": "https://github.com/testuser"}
    link_resp = await client.post(f"/users/{user_id}/links", json=link_data, headers=auth_headers)
    assert link_resp.status_code == 200
    link_id = link_resp.json()["id"]
    
    # Check link in profile
    profile_resp = await client.get(f"/users/{user_id}")
    assert any(link["label"] == "GitHub" for link in profile_resp.json()["links"])
    
    # 4. Delete Link
    del_resp = await client.delete(f"/users/{user_id}/links/{link_id}", headers=auth_headers)
    assert del_resp.status_code == 204

@pytest.mark.asyncio
async def test_user_update_unauthorized(client: AsyncClient, auth_headers: dict):
    # Register another user
    await client.post("/auth/register", json={"username": "victim", "email": "v@e.com", "password": "p"})
    victim_id = 2 # likely 2 if serial
    
    # Try to update victim with our headers
    response = await client.patch(f"/users/{victim_id}", json={"username": "hacker"}, headers=auth_headers)
    assert response.status_code == 403
