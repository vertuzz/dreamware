import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_dream_search_by_tag_name(client: AsyncClient, auth_headers: dict):
    # 1. Create tools and tags
    await client.post("/tools/", json={"name": "Replit"}, headers=auth_headers)
    await client.post("/tags/", json={"name": "Cyberpunk"}, headers=auth_headers)
    await client.post("/tags/", json={"name": "Minimalist"}, headers=auth_headers)
    
    # 2. Get IDs for some
    tag_resp = await client.get("/tags/")
    tags = tag_resp.json()
    cyberpunk_id = [t["id"] for t in tags if t["name"] == "Cyberpunk"][0]
    minimalist_id = [t["id"] for t in tags if t["name"] == "Minimalist"][0]
    
    tool_resp = await client.get("/tools/")
    tools = tool_resp.json()
    replit_id = [t["id"] for t in tools if t["name"] == "Replit"][0]
    
    # 3. Create dreams with different tags/tools
    dream1_data = {
        "prompt_text": "Cyberpunk city dashboard",
        "tool_ids": [replit_id],
        "tag_ids": [cyberpunk_id]
    }
    await client.post("/dreams/", json=dream1_data, headers=auth_headers)
    
    dream2_data = {
        "prompt_text": "Minimalist music player",
        "tag_ids": [minimalist_id]
    }
    await client.post("/dreams/", json=dream2_data, headers=auth_headers)
    
    # 4. Search by tag name
    resp = await client.get("/dreams/?tag=Cyberpunk")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "Cyberpunk" in data[0]["prompt_text"]
    
    resp = await client.get("/dreams/?tag=Minimalist")
    assert len(resp.json()) == 1
    
    # Multiple tags (OR logic)
    resp = await client.get("/dreams/?tag=Cyberpunk,Minimalist")
    assert len(resp.json()) == 2
    
    # Comma with whitespace
    resp = await client.get("/dreams/?tag=Cyberpunk , NonExistent")
    assert len(resp.json()) == 1
    
    # partial match lookup (ilike) only for single values
    resp = await client.get("/dreams/?tag=Cyber")
    assert len(resp.json()) == 1
    
    # 5. Search by tool name
    resp = await client.get("/dreams/?tool=Replit")
    assert len(resp.json()) == 1
    
    # Multiple tools
    await client.post("/tools/", json={"name": "Cursor"}, headers=auth_headers)
    resp = await client.get("/dreams/?tool=Replit,Cursor")
    assert len(resp.json()) == 1 # still 1 because only dream1 has Replit and none have Cursor yet
    
    # 6. Keyword search
    resp = await client.get("/dreams/?search=dashboard")
    assert len(resp.json()) == 1
    
    resp = await client.get("/dreams/?search=player")
    assert len(resp.json()) == 1
    
    resp = await client.get("/dreams/?search=Minimalist")
    assert len(resp.json()) == 1

@pytest.mark.asyncio
async def test_dream_search_no_results(client: AsyncClient):
    resp = await client.get("/dreams/?tag=NonExistent")
    assert resp.status_code == 200
    assert len(resp.json()) == 0
    
    resp = await client.get("/dreams/?tool=NonExistent")
    assert len(resp.json()) == 0
    
    resp = await client.get("/dreams/?search=NonExistent")
    assert len(resp.json()) == 0
