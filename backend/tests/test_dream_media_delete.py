import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_delete_dream_media_comprehensive(client: AsyncClient, auth_headers: dict):
    # 1. Setup: Create a dream
    dream_resp = await client.post(
        "/dreams/", 
        json={"title": "Media Test Dream", "prompt_text": "Testing media deletion"}, 
        headers=auth_headers
    )
    assert dream_resp.status_code == 200
    dream = dream_resp.json()
    dream_id = dream["id"]

    # 2. Add media to the dream
    media_url = "https://example.com/test-image.png"
    media_resp = await client.post(
        f"/dreams/{dream_id}/media", 
        json={"media_url": media_url}, 
        headers=auth_headers
    )
    assert media_resp.status_code == 200
    media = media_resp.json()
    media_id = media["id"]

    # 3. Successful deletion
    delete_resp = await client.delete(
        f"/dreams/{dream_id}/media/{media_id}", 
        headers=auth_headers
    )
    assert delete_resp.status_code == 204

    # 4. Verify it's gone from the dream
    get_resp = await client.get(f"/dreams/{dream_id}")
    assert get_resp.status_code == 200
    updated_dream = get_resp.json()
    assert all(m["id"] != media_id for m in updated_dream.get("media", []))

    # 5. Error: Delete non-existent media
    error_resp = await client.delete(
        f"/dreams/{dream_id}/media/9999", 
        headers=auth_headers
    )
    assert error_resp.status_code == 404

    # 6. Error: Delete media from non-existent dream
    error_resp = await client.delete(
        f"/dreams/9999/media/{media_id}", 
        headers=auth_headers
    )
    assert error_resp.status_code == 404

    # 7. Error: Unauthorized deletion (not the owner)
    # Register another user
    await client.post(
        "/auth/register", 
        json={"username": "other_user", "email": "other@example.com", "password": "password123"}
    )
    login_resp = await client.post(
        "/auth/login", 
        data={"username": "other_user", "password": "password123"}
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Create new media to delete
    media_resp = await client.post(
        f"/dreams/{dream_id}/media", 
        json={"media_url": "https://example.com/another.png"}, 
        headers=auth_headers
    )
    new_media_id = media_resp.json()["id"]

    # Try to delete as other_user
    unauth_resp = await client.delete(
        f"/dreams/{dream_id}/media/{new_media_id}", 
        headers=other_headers
    )
    assert unauth_resp.status_code == 403
