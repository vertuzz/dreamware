import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_dream_lifecycle(client: AsyncClient, auth_headers: dict):
    # 1. Create tools and tags first (admin-like public for now)
    tool_resp = await client.post("/tools/", json={"name": "Cursor"}, headers=auth_headers)
    tag_resp = await client.post("/tags/", json={"name": "SaaS"}, headers=auth_headers)
    tool_id = tool_resp.json()["id"]
    tag_id = tag_resp.json()["id"]
    
    # 2. Create Dream
    dream_data = {
        "prompt_text": "A minimal todo app with neon colors",
        "prd_text": "Full PRD details here",
        "status": "Concept",
        "tool_ids": [tool_id],
        "tag_ids": [tag_id]
    }
    response = await client.post("/dreams/", json=dream_data, headers=auth_headers)
    assert response.status_code == 200
    dream_id = response.json()["id"]
    assert response.json()["prompt_text"] == dream_data["prompt_text"]
    
    # 3. Fork Dream
    fork_resp = await client.post(f"/dreams/{dream_id}/fork", headers=auth_headers)
    assert fork_resp.status_code == 200
    assert fork_resp.json()["parent_dream_id"] == dream_id
    
    # 4. Social interaction (Comment & Review)
    comment_resp = await client.post(f"/dreams/{dream_id}/comments", json={"content": "Cool dream!"}, headers=auth_headers)
    assert comment_resp.status_code == 200
    
    review_resp = await client.post(f"/dreams/{dream_id}/reviews", json={"score": 85.5, "comment": "Great prompt"}, headers=auth_headers)
    assert review_resp.status_code == 200
    
    # Check avg score
    avg_resp = await client.get(f"/dreams/{dream_id}/avg-score")
    assert avg_resp.json()["average_score"] == 85.5
    
    # 5. Like
    like_resp = await client.post(f"/dreams/{dream_id}/like", headers=auth_headers)
    assert like_resp.status_code == 200
    
    # 6. Implementation
    impl_data = {"url": "https://neon-todo.vercel.app", "description": "Built in 10 mins"}
    impl_resp = await client.post(f"/dreams/{dream_id}/implementations", json=impl_data, headers=auth_headers)
    assert impl_resp.status_code == 200
    impl_id = impl_resp.json()["id"]
    
    # Mark official
    await client.patch(f"/implementations/{impl_id}/official", headers=auth_headers)
    
    # Final check: Feed
    feed_resp = await client.get("/dreams/")
    assert len(feed_resp.json()) >= 1
