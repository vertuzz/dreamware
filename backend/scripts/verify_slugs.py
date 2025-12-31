import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def verify_endpoints():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        print("Verifying Dream by Slug...")
        # "Neon Dreams Dashboard" -> "neon-dreams-dashboard"
        response = await client.get("/dreams/neon-dreams-dashboard")
        if response.status_code == 200:
            print("SUCCESS: Found dream by slug")
            print(f"Dream ID: {response.json()['id']}, Slug: {response.json().get('slug')}")
            dream_id = response.json()['id']
        else:
            print(f"FAILURE: Could not find dream by slug. Status: {response.status_code}")
            print(response.text)
            return

        print("\nVerifying Dream by ID...")
        response = await client.get(f"/dreams/{dream_id}")
        if response.status_code == 200:
             print("SUCCESS: Found dream by ID")
        else:
             print(f"FAILURE: Could not find dream by ID. Status: {response.status_code}")

        print("\nVerifying User by Username...")
        response = await client.get("/users/admin")
        if response.status_code == 200:
            print("SUCCESS: Found user by username")
            print(f"User ID: {response.json()['id']}, Username: {response.json()['username']}")
            user_id = response.json()['id']
        else:
             print(f"FAILURE: Could not find user by username. Status: {response.status_code}")
             print(response.text)
             return

        print("\nVerifying User by ID...")
        response = await client.get(f"/users/{user_id}")
        if response.status_code == 200:
             print("SUCCESS: Found user by ID")
        else:
             print(f"FAILURE: Could not find user by ID. Status: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(verify_endpoints())
