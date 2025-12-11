"""Quick webhook test."""
import requests
print("Testing webhook...")
try:
    response = requests.post(
        "http://localhost:8000/api/webhooks/github",
        json={"test": "data"},
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": "sha256=invalid"
        },
        timeout=5
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ SUCCESS! Invalid signature was REJECTED!")
    elif response.status_code == 200:
        print("❌ FAIL - should have rejected invalid signature")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
