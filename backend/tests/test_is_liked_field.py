import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_dreams_is_liked_field(client: AsyncClient, auth_headers: dict):
    # Setup: Create a dream
    dream_resp = await client.post(
        "/dreams/", 
        json={"prompt_text": "Test Dream for is_liked check"}, 
        headers=auth_headers
    )
    assert dream_resp.status_code == 200
    dream_id = dream_resp.json()["id"]

    # 1. Verify initial status (is_liked=False)
    # Check List endpoint
    list_resp = await client.get("/dreams/", headers=auth_headers)
    assert list_resp.status_code == 200
    dreams = list_resp.json()
    our_dream = next(d for d in dreams if d["id"] == dream_id)
    assert our_dream["is_liked"] is False

    # Check Detail endpoint
    detail_resp = await client.get(f"/dreams/{dream_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["is_liked"] is False

    # 2. Like the dream
    like_resp = await client.post(f"/dreams/{dream_id}/like", headers=auth_headers)
    assert like_resp.status_code == 200

    # 3. Verify updated status (is_liked=True)
    # Check List endpoint
    list_resp_2 = await client.get("/dreams/", headers=auth_headers)
    assert list_resp_2.status_code == 200
    dreams_2 = list_resp_2.json()
    our_dream_2 = next(d for d in dreams_2 if d["id"] == dream_id)
    assert our_dream_2["is_liked"] is True

    # Check Detail endpoint
    detail_resp_2 = await client.get(f"/dreams/{dream_id}", headers=auth_headers)
    assert detail_resp_2.status_code == 200
    assert detail_resp_2.json()["is_liked"] is True

    # 4. Unlike the dream
    unlike_resp = await client.delete(f"/dreams/{dream_id}/like", headers=auth_headers)
    assert unlike_resp.status_code == 200

    # 5. Verify reverted status (is_liked=False)
    detail_resp_3 = await client.get(f"/dreams/{dream_id}", headers=auth_headers)
    assert detail_resp_3.status_code == 200
    assert detail_resp_3.json()["is_liked"] is False
