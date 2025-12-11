"""Quick test to verify webhook signature validation is working."""
import requests
import hmac
import hashlib
import json
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
WEBHOOK_URL = "http://localhost:8000/api/webhooks/github"

# Simple test payload
test_payload = {"test": "data"}
payload_bytes = json.dumps(test_payload).encode()

print(f"🔐 Testing with secret: {WEBHOOK_SECRET[:10]}...")
print()

# Test 1: Valid signature
print("1️⃣ Testing VALID signature...")
valid_sig = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()
response = requests.post(
    WEBHOOK_URL,
    json=test_payload,
    headers={"X-Hub-Signature-256": valid_sig, "X-GitHub-Event": "ping"}
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
print(f"   {'✅ PASS' if response.status_code == 200 else '❌ FAIL'}")
print()

# Test 2: Invalid signature  
print("2️⃣ Testing INVALID signature...")
invalid_sig = "sha256=invalid_hash_12345"
response = requests.post(
    WEBHOOK_URL,
    json=test_payload,
    headers={"X-Hub-Signature-256": invalid_sig, "X-GitHub-Event": "ping"}
)
print(f"   Status: {response.status_code}")
if response.status_code == 401:
    print(f"   Response: {response.json()}")
    print(f"   ✅ PASS - Correctly rejected")
else:
    print(f"   ❌ FAIL - Should have rejected with 401, got {response.status_code}")
