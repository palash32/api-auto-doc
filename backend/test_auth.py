"""Test what user the API auth returns"""
import requests
import json

# Test the repositories endpoint
print("Testing /api/repositories/ endpoint...")
response = requests.get("http://localhost:8000/api/repositories/")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
print()

# Test the root endpoint to see app info
print("Testing / endpoint...")
response = requests.get("http://localhost:8000/")
print(f"Response: {json.dumps(response.json(), indent=2)}")
