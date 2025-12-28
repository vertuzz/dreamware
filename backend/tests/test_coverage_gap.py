import pytest
from httpx import AsyncClient
import pytest

@pytest.mark.asyncio
async def test_dreams_filtering_and_errors(client: AsyncClient, auth_headers: dict):
    # Setup: Create tool, tag and dreams
    t_resp = await client.post("/tools/", json={"name": "Tailwind"}, headers=auth_headers)
    tool_id = t_resp.json()["id"]
    tag_resp = await client.post("/tags/", json={"name": "UI"}, headers=auth_headers)
    tag_id = tag_resp.json()["id"]

    v1_resp = await client.post("/dreams/", json={"prompt_text": "V1", "tool_ids": [tool_id], "status": "Concept"}, headers=auth_headers)
    v1 = v1_resp.json()
    v2_resp = await client.post("/dreams/", json={"prompt_text": "V2", "tag_ids": [tag_id], "status": "WIP"}, headers=auth_headers)
    v2 = v2_resp.json()

    # 1. Filter by tool
    resp = await client.get(f"/dreams/?tool_id={tool_id}")
    assert len(resp.json()) >= 1
    assert any(v["id"] == v1["id"] for v in resp.json())

    # 2. Filter by tag
    resp = await client.get(f"/dreams/?tag_id={tag_id}")
    assert len(resp.json()) >= 1
    assert any(v["id"] == v2["id"] for v in resp.json())

    # 3. Filter by status
    resp = await client.get("/dreams/?status=WIP")
    assert all(v["status"] == "WIP" for v in resp.json())

    # 4. Error: Get non-existent dream
    resp = await client.get("/dreams/9999")
    assert resp.status_code == 404

    # 5. Error: Update non-existent dream
    resp = await client.patch("/dreams/9999", json={"prompt_text": "new"}, headers=auth_headers)
    assert resp.status_code == 404

    # 6. Error: Update others' dream
    # Register another user to own a dream
    await client.post("/auth/register", json={"username": "other", "email": "other@v.com", "password": "p"})
    # Login as other to create a dream
    login_resp = await client.post("/auth/login", data={"username": "other", "password": "p"})
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    other_dream_resp = await client.post("/dreams/", json={"prompt_text": "Other Dream"}, headers=other_headers)
    other_dream = other_dream_resp.json()

    # Try to update other_dream with original auth_headers
    resp = await client.patch(f"/dreams/{other_dream['id']}", json={"prompt_text": "hacked"}, headers=auth_headers)
    assert resp.status_code == 403

    # 7. Error: Fork non-existent dream
    resp = await client.post("/dreams/9999/fork", headers=auth_headers)
    assert resp.status_code == 404

    # 8. Error: Add image to others' dream
    resp = await client.post(f"/dreams/{other_dream['id']}/images", json={"image_url": "http://evil.com"}, headers=auth_headers)
    assert resp.status_code == 403

    # 9. Success: Update own dream
    resp = await client.patch(f"/dreams/{v1['id']}", json={"prompt_text": "Updated V1"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["prompt_text"] == "Updated V1"

    # 10. Success: Get dream
    resp = await client.get(f"/dreams/{v1['id']}")
    assert resp.status_code == 200

    # 11. Success: Add image to own dream
    resp = await client.post(f"/dreams/{v1['id']}/images", json={"image_url": "http://mydream.com/img.png"}, headers=auth_headers)
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_likes_errors_and_unlikes(client: AsyncClient, auth_headers: dict):
    # Setup dream
    dream_resp = await client.post("/dreams/", json={"prompt_text": "Like Me"}, headers=auth_headers)
    dream = dream_resp.json()
    dream_id = dream["id"]

    # 1. Like dream
    await client.post(f"/dreams/{dream_id}/like", headers=auth_headers)
    
    # 2. Duplicate like (400)
    resp = await client.post(f"/dreams/{dream_id}/like", headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Already liked"

    # 3. Unlike dream
    resp = await client.delete(f"/dreams/{dream_id}/like", headers=auth_headers)
    assert resp.status_code == 200
    
    # 4. Unlike again (404)
    resp = await client.delete(f"/dreams/{dream_id}/like", headers=auth_headers)
    assert resp.status_code == 404

    # 5. Like comment
    comm_resp = await client.post(f"/dreams/{dream_id}/comments", json={"content": "Liking this"}, headers=auth_headers)
    comm = comm_resp.json()
    comm_id = comm["id"]
    resp = await client.post(f"/comments/{comm_id}/like", headers=auth_headers)
    assert resp.status_code == 200

    # 6. Duplicate comment like
    resp = await client.post(f"/comments/{comm_id}/like", headers=auth_headers)
    assert resp.status_code == 400

    # 7. Dream not found for like
    assert (await client.post("/dreams/9999/like", headers=auth_headers)).status_code == 404

    # 8. Comment not found for like
    assert (await client.post("/comments/9999/like", headers=auth_headers)).status_code == 404

@pytest.mark.asyncio
async def test_notifications_read(client: AsyncClient, auth_headers: dict):
    # 1. Register a victim (the one who will receive the notification)
    await client.post("/auth/register", json={"username": "victim_n", "email": "vn@v.com", "password": "p"})
    login_resp = await client.post("/auth/login", data={"username": "victim_n", "password": "p"})
    victim_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    # Victim creates a dream
    dream_resp = await client.post("/dreams/", json={"prompt_text": "Notify me"}, headers=victim_headers)
    dream = dream_resp.json()

    # 2. Origin user (auth_headers) likes victim's dream
    await client.post(f"/dreams/{dream['id']}/like", headers=auth_headers)

    # 3. Check notification for victim
    n_resp = await client.get("/notifications/", headers=victim_headers)
    assert len(n_resp.json()) >= 1
    n_id = n_resp.json()[0]["id"]

    # Mark as read
    resp = await client.patch(f"/notifications/{n_id}/read", headers=victim_headers)
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True

    # 4. Error: Notification not found (or not yours)
    resp = await client.patch(f"/notifications/{n_id}/read", headers=auth_headers)
    assert resp.status_code == 404

    # 5. Success: Mark all read
    resp = await client.patch("/notifications/read-all", headers=victim_headers)
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_reviews_and_comments_errors(client: AsyncClient, auth_headers: dict):
    dream_resp = await client.post("/dreams/", json={"prompt_text": "Err Dream"}, headers=auth_headers)
    dream = dream_resp.json()
    dream_id = dream["id"]

    # 1. Comment not found
    assert (await client.patch("/comments/9999", json={"content": "x"}, headers=auth_headers)).status_code == 404
    assert (await client.delete("/comments/9999", headers=auth_headers)).status_code == 404

    # 2. Unauthorized comment edit
    await client.post("/auth/register", json={"username": "comm_owner", "email": "co@v.com", "password": "p"})
    login_resp = await client.post("/auth/login", data={"username": "comm_owner", "password": "p"})
    co_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    comm_resp = await client.post(f"/dreams/{dream_id}/comments", json={"content": "Mine"}, headers=co_headers)
    comm = comm_resp.json()

    assert (await client.patch(f"/comments/{comm['id']}", json={"content": "hacked"}, headers=auth_headers)).status_code == 403

    # 3. Success: Update own comment
    resp = await client.patch(f"/comments/{comm['id']}", json={"content": "Actually mine"}, headers=co_headers)
    assert resp.status_code == 200
    assert resp.json()["content"] == "Actually mine"

    # 4. Success: Get dream comments
    resp = await client.get(f"/dreams/{dream_id}/comments")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 5. Success: Delete own comment
    resp = await client.delete(f"/comments/{comm['id']}", headers=co_headers)
    assert resp.status_code == 204

    # 6. Error: Create comment on missing dream
    resp = await client.post("/dreams/9999/comments", json={"content": "lost"}, headers=auth_headers)
    assert resp.status_code == 404

    # 7. Error: Delete others' comment
    comm2_resp = await client.post(f"/dreams/{dream_id}/comments", json={"content": "Another"}, headers=auth_headers)
    comm2 = comm2_resp.json()
    assert (await client.delete(f"/comments/{comm2['id']}", headers= co_headers)).status_code == 403

@pytest.mark.asyncio
async def test_collections_edge_cases(client: AsyncClient, auth_headers: dict):
    dream_resp = await client.post("/dreams/", json={"prompt_text": "In Col"}, headers=auth_headers)
    dream = dream_resp.json()
    
    # 1. Create collection
    col_resp = await client.post("/collections/", json={"name": "My Pack", "dream_ids": [dream["id"]]}, headers=auth_headers)
    col = col_resp.json()
    
    # 2. Add non-existent dream to collection
    resp = await client.post(f"/collections/{col['id']}/dreams/9999", headers=auth_headers)
    assert resp.status_code == 404

    # 3. Add to non-existent collection
    resp = await client.post(f"/collections/9999/dreams/{dream['id']}", headers=auth_headers)
    assert resp.status_code == 404

    # 4. Add to someone else's collection
    await client.post("/auth/register", json={"username": "col_owner", "email": "col@v.com", "password": "p"})
    login_resp = await client.post("/auth/login", data={"username": "col_owner", "password": "p"})
    col_owner_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    resp = await client.post(f"/collections/{col['id']}/dreams/{dream['id']}", headers=col_owner_headers)
    assert resp.status_code == 404 # It returns 404 because query filters by owner_id

    # 5. Get private collection
    priv_col_resp = await client.post("/collections/", json={"name": "Secret", "is_public": False}, headers=auth_headers)
    priv_col = priv_col_resp.json()
    
    # Unauthorized access (no token) should be 403 (or 401 depending on how we want it, but code says 403 if not authorized)
    resp = await client.get(f"/collections/{priv_col['id']}")
    assert resp.status_code == 403
    
    # Authorized access (owner) should be 200
    resp = await client.get(f"/collections/{priv_col['id']}", headers=auth_headers)
    assert resp.status_code == 200
    
    # Unauthorized access (another user) should be 403
    resp = await client.get(f"/collections/{priv_col['id']}", headers=col_owner_headers)
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_reviews_comprehensive(client: AsyncClient, auth_headers: dict):
    dream_resp = await client.post("/dreams/", json={"prompt_text": "Review Hub"}, headers=auth_headers)
    dream = dream_resp.json()
    dream_id = dream["id"]

    # 1. Create review
    review_resp = await client.post(f"/dreams/{dream_id}/reviews", json={"score": 90, "comment": "Good"}, headers=auth_headers)
    review = review_resp.json()
    
    # 2. Duplicate review
    resp = await client.post(f"/dreams/{dream_id}/reviews", json={"score": 80}, headers=auth_headers)
    assert resp.status_code == 400

    # 3. Delete review - Unauthorized
    await client.post("/auth/register", json={"username": "not_reviewer", "email": "nr@v.com", "password": "p"})
    login_resp = await client.post("/auth/login", data={"username": "not_reviewer", "password": "p"})
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    
    resp = await client.delete(f"/reviews/{review['id']}", headers=other_headers)
    assert resp.status_code == 403

    # 4. Delete review - Not found
    assert (await client.delete("/reviews/9999", headers=auth_headers)).status_code == 404

    # 5. Delete review - Happy path
    assert (await client.delete(f"/reviews/{review['id']}", headers=auth_headers)).status_code == 204

@pytest.mark.asyncio
async def test_follows_and_impls_edge_cases(client: AsyncClient, auth_headers: dict):
    # Setup
    me_resp = await client.get("/auth/me", headers=auth_headers)
    me = me_resp.json()
    
    # 1. Follow self
    resp = await client.post(f"/users/{me['id']}/follow", headers=auth_headers)
    assert resp.status_code == 400

    # 2. Follow non-existent
    assert (await client.post("/users/9999/follow", headers=auth_headers)).status_code == 404

    # 3. Already following
    await client.post("/auth/register", json={"username": "star", "email": "s@v.com", "password": "p"})
    star_resp = await client.post("/auth/login", data={"username": "star", "password": "p"})
    star = star_resp.json()
    star_id = 4 # Incremental
    # Let's get actual ID
    star_info_resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {star['access_token']}"})
    star_info = star_info_resp.json()
    star_id = star_info["id"]

    await client.post(f"/users/{star_id}/follow", headers=auth_headers)
    assert (await client.post(f"/users/{star_id}/follow", headers=auth_headers)).status_code == 400

    # 4. Unfollow not following
    assert (await client.delete("/users/9999/follow", headers=auth_headers)).status_code == 404

    # 5. Implementation - Dream not found
    assert (await client.post("/dreams/9999/implementations", json={"url": "http://x.com"}, headers=auth_headers)).status_code == 404

    # 6. Mark official - Not found
    assert (await client.patch("/implementations/9999/official", headers=auth_headers)).status_code == 404

    # 7. Mark official - Unauthorized
    dream_resp = await client.post("/dreams/", json={"prompt_text": "Official Dream"}, headers=auth_headers)
    dream = dream_resp.json()
    # Someone else implements it
    other_headers = {"Authorization": f"Bearer {star['access_token']}"}
    impl_resp = await client.post(f"/dreams/{dream['id']}/implementations", json={"url": "http://impl.com"}, headers=other_headers)
    impl = impl_resp.json()
    
    # Other user tries to mark it official (only dream creator can)
    resp = await client.patch(f"/implementations/{impl['id']}/official", headers=other_headers)
    assert resp.status_code == 403
