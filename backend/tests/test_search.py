from fastapi.testclient import TestClient

def test_vibe_search_by_tag_name(client: TestClient, auth_headers: dict):
    # 1. Create tools and tags
    client.post("/tools/", json={"name": "Replit"})
    client.post("/tags/", json={"name": "Cyberpunk"})
    client.post("/tags/", json={"name": "Minimalist"})
    
    # 2. Get IDs for some
    tag_resp = client.get("/tags/")
    tags = tag_resp.json()
    cyberpunk_id = [t["id"] for t in tags if t["name"] == "Cyberpunk"][0]
    minimalist_id = [t["id"] for t in tags if t["name"] == "Minimalist"][0]
    
    tool_resp = client.get("/tools/")
    tools = tool_resp.json()
    replit_id = [t["id"] for t in tools if t["name"] == "Replit"][0]
    
    # 3. Create vibes with different tags/tools
    vibe1_data = {
        "prompt_text": "Cyberpunk city dashboard",
        "tool_ids": [replit_id],
        "tag_ids": [cyberpunk_id]
    }
    client.post("/vibes/", json=vibe1_data, headers=auth_headers)
    
    vibe2_data = {
        "prompt_text": "Minimalist music player",
        "tag_ids": [minimalist_id]
    }
    client.post("/vibes/", json=vibe2_data, headers=auth_headers)
    
    # 4. Search by tag name
    resp = client.get("/vibes/?tag=Cyberpunk")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "Cyberpunk" in data[0]["prompt_text"]
    
    resp = client.get("/vibes/?tag=Minimalist")
    assert len(resp.json()) == 1
    
    # Multiple tags (OR logic)
    resp = client.get("/vibes/?tag=Cyberpunk,Minimalist")
    assert len(resp.json()) == 2
    
    # Comma with whitespace
    resp = client.get("/vibes/?tag=Cyberpunk , NonExistent")
    assert len(resp.json()) == 1
    
    # partial match lookup (ilike) only for single values
    resp = client.get("/vibes/?tag=Cyber")
    assert len(resp.json()) == 1
    
    # 5. Search by tool name
    resp = client.get("/vibes/?tool=Replit")
    assert len(resp.json()) == 1
    
    # Multiple tools
    client.post("/tools/", json={"name": "Cursor"})
    resp = client.get("/vibes/?tool=Replit,Cursor")
    assert len(resp.json()) == 1 # still 1 because only vibe1 has Replit and none have Cursor yet
    
    # 6. Keyword search
    resp = client.get("/vibes/?search=dashboard")
    assert len(resp.json()) == 1
    
    resp = client.get("/vibes/?search=player")
    assert len(resp.json()) == 1
    
    resp = client.get("/vibes/?search=Minimalist")
    assert len(resp.json()) == 1

def test_vibe_search_no_results(client: TestClient):
    resp = client.get("/vibes/?tag=NonExistent")
    assert resp.status_code == 200
    assert len(resp.json()) == 0
    
    resp = client.get("/vibes/?tool=NonExistent")
    assert len(resp.json()) == 0
    
    resp = client.get("/vibes/?search=NonExistent")
    assert len(resp.json()) == 0
