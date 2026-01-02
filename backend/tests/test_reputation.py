import pytest
from httpx import AsyncClient

async def get_auth_headers(client: AsyncClient, username: str):
    email = f"{username}@example.com"
    password = "password123"
    await client.post("/auth/register", json={"username": username, "email": email, "password": password})
    response = await client.post("/auth/login", data={"username": username, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_reputation_flow(client: AsyncClient):
    # Setup two users
    headers_a = await get_auth_headers(client, "user_a")
    headers_b = await get_auth_headers(client, "user_b")
    
    # Get user_a info
    user_a_initial = (await client.get("/users/user_a")).json()
    assert user_a_initial["reputation_score"] == 0.0
    
    # 1. Test Follow Reputation (+5)
    await client.post(f"/users/{user_a_initial['id']}/follow", headers=headers_b)
    user_a_after_follow = (await client.get("/users/user_a")).json()
    assert user_a_after_follow["reputation_score"] == 5.0
    
    # 2. Test Unfollow Reputation (-5)
    await client.delete(f"/users/{user_a_initial['id']}/follow", headers=headers_b)
    user_a_after_unfollow = (await client.get("/users/user_a")).json()
    assert user_a_after_unfollow["reputation_score"] == 0.0
    
    # 3. Test Like Reputation (+2)
    # User A creates a dream
    dream_resp = await client.post("/dreams/", json={"prompt_text": "Reputation Dream"}, headers=headers_a)
    dream_id = dream_resp.json()["id"]
    
    # User B likes it
    await client.post(f"/dreams/{dream_id}/like", headers=headers_b)
    user_a_after_like = (await client.get("/users/user_a")).json()
    assert user_a_after_like["reputation_score"] == 2.0
    
    # User B unlikes it
    await client.delete(f"/dreams/{dream_id}/like", headers=headers_b)
    user_a_after_unlike = (await client.get("/users/user_a")).json()
    assert user_a_after_unlike["reputation_score"] == 0.0
    
    # 4. Test Comment Reputation (+1 per upvote)
    # User A comments on their dream
    comment_resp = await client.post(f"/dreams/{dream_id}/comments", json={"content": "Reputation Comment"}, headers=headers_a)
    comment_id = comment_resp.json()["id"]
    
    # User B upvotes it
    await client.post(f"/comments/{comment_id}/vote?value=1", headers=headers_b)
    user_a_after_vote = (await client.get("/users/user_a")).json()
    assert user_a_after_vote["reputation_score"] == 1.0
    
    # User B downvotes it (flip from +1 to -1, which is -2 delta)
    await client.post(f"/comments/{comment_id}/vote?value=-1", headers=headers_b)
    user_a_after_downvote = (await client.get("/users/user_a")).json()
    assert user_a_after_downvote["reputation_score"] == -1.0
    
    # User B removes vote (delta +1 from -1 to 0)
    await client.post(f"/comments/{comment_id}/vote?value=0", headers=headers_b)
    user_a_final = (await client.get("/users/user_a")).json()
    assert user_a_final["reputation_score"] == 0.0

@pytest.mark.asyncio
async def test_self_action_reputation(client: AsyncClient):
    headers_a = await get_auth_headers(client, "self_user")
    
    # User A creates a dream and a comment
    dream_resp = await client.post("/dreams/", json={"prompt_text": "Self Dream"}, headers=headers_a)
    dream_id = dream_resp.json()["id"]
    
    comment_resp = await client.post(f"/dreams/{dream_id}/comments", json={"content": "Self Comment"}, headers=headers_a)
    comment_id = comment_resp.json()["id"]
    
    # Self like (should not work if API prevents it, but let's check reputation if it happens)
    # The API doesn't seem to explicitly forbid self-liking in likes.py, but it should not update reputation
    await client.post(f"/dreams/{dream_id}/like", headers=headers_a)
    user_after_self_like = (await client.get("/users/self_user")).json()
    assert user_after_self_like["reputation_score"] == 0.0
    
    # Self vote
    await client.post(f"/comments/{comment_id}/vote?value=1", headers=headers_a)
    user_after_self_vote = (await client.get("/users/self_user")).json()
    assert user_after_self_vote["reputation_score"] == 0.0
