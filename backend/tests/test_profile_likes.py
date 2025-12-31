import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_liked_by_user_id_filter(client: AsyncClient, auth_headers: dict):
    # 1. Create a dream
    dream_resp = await client.post(
        "/dreams/", 
        json={"title": "Dream to be Liked", "prompt_text": "Filter test"}, 
        headers=auth_headers
    )
    assert dream_resp.status_code == 200
    dream_id = dream_resp.json()["id"]

    # 2. Like the dream
    like_resp = await client.post(f"/dreams/{dream_id}/like", headers=auth_headers)
    assert like_resp.status_code == 200

    # 3. Get user info to get the ID
    user_resp = await client.get("/auth/me", headers=auth_headers)
    assert user_resp.status_code == 200
    user_id = user_resp.json()["id"]

    # 4. Filter by liked_by_user_id
    filter_resp = await client.get(f"/dreams/?liked_by_user_id={user_id}", headers=auth_headers)
    assert filter_resp.status_code == 200
    dreams = filter_resp.json()
    assert len(dreams) >= 1
    assert any(d["id"] == dream_id for d in dreams)

    # 5. Filter by a different user ID (should not return this dream)
    filter_resp_other = await client.get("/dreams/?liked_by_user_id=99999", headers=auth_headers)
    assert filter_resp_other.status_code == 200
    dreams_other = filter_resp_other.json()
    assert not any(d["id"] == dream_id for d in dreams_other)
