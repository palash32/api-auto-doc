"""Test API endpoint for repositories"""
import requests
import json

url = "http://localhost:8000/api/repositories/"
response = requests.get(url)

print(f"Status Code: {response.status_code}")
print(f"Response Length: {len(response.text)}")
print(f"\nResponse Content:")
print(json.dumps(response.json(), indent=2))
