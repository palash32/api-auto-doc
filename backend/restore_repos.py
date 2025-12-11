"""Re-add the 7 repositories that were previously added"""
import requests
import time

# List of repository URLs to re-add
repos = [
    "https://github.com/fastapi/fastapi-hello-world",
    "https://github.com/encode/starlette",
    "https://github.com/palash32/Blogging-App",
    "https://github.com/palash32/telegram-clone",
    "https://github.com/palash32/smart_dustbin",
    "https://github.com/octocat/Spoon-Knife",
    "https://github.com/palash32/Payment_Gateway_Integration"
]

base_url = "http://localhost:8000"

print(f"Re-adding {len(repos)} repositories...\n")

for i, repo_url in enumerate(repos, 1):
    print(f"{i}. Adding: {repo_url}")
    
    try:
        response = requests.post(
            f"{base_url}/api/repositories/",
            params={"url": repo_url}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Added: {data.get('name', 'unknown')}")
        else:
            print(f"   ❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Small delay to avoid overwhelming the API
    time.sleep(0.5)

print(f"\n✅ Finished re-adding repositories!")
print(f"\nCheck the API:")
try:
    response = requests.get(f"{base_url}/api/repositories/")
    repos_list = response.json()
    print(f"Total repositories now: {len(repos_list)}")
except Exception as e:
    print(f"Error checking: {e}")
