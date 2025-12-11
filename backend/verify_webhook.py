import asyncio
import hmac
import hashlib
import json
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
WEBHOOK_URL = "http://localhost:8000/api/webhooks/github"
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "test_secret_123")  # Read from .env

# Sample push event payload
PUSH_PAYLOAD = {
    "ref": "refs/heads/main",
    "repository": {
        "full_name": "encode/starlette",  # Use the repo we have in DB
        "name": "starlette",
        "owner": {"login": "encode"}
    },
    "pusher": {"name": "test-user"},
    "commits": [
        {
            "id": "abc123",
            "message": "Update documentation",
            "author": {"name": "Test User"}
        }
    ]
}

def generate_signature(payload: dict, secret: str) -> str:
    """Generate HMAC signature like GitHub does."""
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode()
    signature = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

async def test_webhook():
    print("🚀 Testing GitHub Webhook Endpoint...")
    
    # 1. Test ping event
    print("\n1️⃣ Testing PING event...")
    ping_payload = {"zen": "Design for failure."}
    signature = generate_signature(ping_payload, WEBHOOK_SECRET)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            WEBHOOK_URL,
            json=ping_payload,
            headers={
                "X-GitHub-Event": "ping",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print(f"✅ Ping: {response.json()}")
        else:
            print(f"❌ Ping failed: {response.status_code} - {response.text}")
    
    # 2. Test push event (valid signature)
    print("\n2️⃣ Testing PUSH event (valid signature)...")
    signature = generate_signature(PUSH_PAYLOAD, WEBHOOK_SECRET)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            WEBHOOK_URL,
            json=PUSH_PAYLOAD,
            headers={
                "X-GitHub-Event": "push",
                "X-Hub-Signature-256": signature,
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Push: {result}")
            if result.get("message") == "scan triggered":
                print("   🎉 Scan was triggered successfully!")
        else:
            print(f"❌ Push failed: {response.status_code} - {response.text}")
    
    # 3. Test invalid signature
    print("\n3️⃣ Testing INVALID signature (should reject)...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            WEBHOOK_URL,
            json=PUSH_PAYLOAD,
            headers={
                "X-GitHub-Event": "push",
                "X-Hub-Signature-256": "sha256=INVALID_SIGNATURE",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 401:
            print("✅ Invalid signature correctly rejected")
        else:
            print(f"❌ Should have rejected invalid signature, got: {response.status_code}")

if __name__ == "__main__":
    print("⚠️  Make sure:")
    print("   1. Backend is running (uvicorn app.main:app --reload)")
    print(f"   2. GITHUB_WEBHOOK_SECRET='{WEBHOOK_SECRET}' in .env")
    print("   3. Repository 'encode/starlette' exists in DB")
    print()
    
    asyncio.run(test_webhook())
