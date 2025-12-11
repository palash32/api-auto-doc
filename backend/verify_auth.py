"""
Verification script for Auth Endpoints.
Mocks GitHub API responses to test the callback flow locally.
"""
import asyncio
import httpx
from unittest.mock import MagicMock, patch
from app.api.auth import github_callback
from app.core.security import verify_token
from app.core.database import AsyncSessionLocal

async def test_auth_flow():
    print("🚀 Starting Auth Flow Verification...")
    
    # Mock settings
    with patch("app.core.config.settings.GITHUB_CLIENT_ID", "mock_client_id"), \
         patch("app.core.config.settings.GITHUB_CLIENT_SECRET", "mock_secret"), \
         patch("app.core.config.settings.GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/github/callback"):
        
        # 1. Test Login Redirect URL generation
        from app.api.auth import github_login
        response = await github_login()
        print(f"✅ Login Endpoint: Redirects to {response.headers['location'][:50]}...")
        
        # 2. Test Callback (Mocking GitHub)
        print("\n🔄 Testing Callback Flow (Mocking GitHub)...")
    
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"access_token": "mock_gh_token_123"}
    
    mock_user_resp = MagicMock()
    mock_user_resp.status_code = 200
    mock_user_resp.json.return_value = {
        "login": "testuser",
        "email": "test@example.com",
        "name": "Test User"
    }
    
    # Patch httpx.AsyncClient to mock GitHub calls
    with patch("httpx.AsyncClient.post", return_value=mock_token_resp) as mock_post, \
         patch("httpx.AsyncClient.get", return_value=mock_user_resp) as mock_get:
        
        async with AsyncSessionLocal() as db:
            # Call the callback endpoint directly
            try:
                response = await github_callback(code="mock_code", db=db)
                
                # Extract JWT from redirect URL
                redirect_url = response.headers["location"]
                print(f"✅ Callback Success: Redirects to frontend")
                
                import re
                token_match = re.search(r"token=([^&]+)", redirect_url)
                if token_match:
                    jwt_token = token_match.group(1)
                    print(f"🔑 JWT Token Generated: {jwt_token[:20]}...")
                    
                    # 3. Verify Token
                    payload = verify_token(jwt_token)
                    print(f"✅ Token Verified: User ID {payload['sub']}")
                else:
                    print("❌ Failed to extract token from redirect URL")
            except Exception as e:
                print(f"❌ Callback Failed: {str(e)}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
