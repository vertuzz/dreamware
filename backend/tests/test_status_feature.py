import pytest
from httpx import AsyncClient
from app.models import DreamStatus

@pytest.mark.asyncio
async def test_status_filtering(client: AsyncClient, auth_headers: dict):
    # 1. Create a Concept dream
    await client.post("/dreams/", json={
        "title": "Concept Dream",
        "status": "Concept"
    }, headers=auth_headers)
    
    # 2. Create a Live dream
    await client.post("/dreams/", json={
        "title": "Live Dream",
        "status": "Live"
    }, headers=auth_headers)
    
    # 3. Filter by Concept
    resp = await client.get("/dreams/", params={"status": "Concept"})
    assert resp.status_code == 200
    concepts = [d for d in resp.json() if d["title"] in ["Concept Dream", "Live Dream"]]
    assert len(concepts) >= 1
    assert all(d["status"] == "Concept" for d in concepts)
    
    # 4. Filter by Live
    resp = await client.get("/dreams/", params={"status": "Live"})
    assert resp.status_code == 200
    lives = [d for d in resp.json() if d["title"] in ["Concept Dream", "Live Dream"]]
    assert len(lives) >= 1
    assert all(d["status"] == "Live" for d in lives)

@pytest.mark.asyncio
async def test_manual_status_update(client: AsyncClient, auth_headers: dict):
    # 1. Create dream
    resp = await client.post("/dreams/", json={
        "title": "Status Test",
        "status": "Concept"
    }, headers=auth_headers)
    dream_id = resp.json()["id"]
    
    # 2. Update to WIP
    resp = await client.patch(f"/dreams/{dream_id}", json={"status": "WIP"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "WIP"
    
    # 3. Update to Live
    resp = await client.patch(f"/dreams/{dream_id}", json={"status": "Live"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "Live"
