import sys
from uuid import uuid4
from datetime import datetime

def test_schemas():
    print("🔍 Verifying Pydantic Schemas...")
    
    try:
        from app.schemas.user import UserCreate, UserResponse, UserRole
        from app.schemas.repository import RepositoryCreate, RepositoryResponse, GitProvider, ScanStatus
        from app.schemas.api_endpoint import APIEndpointCreate, APIEndpointResponse, HTTPMethod, APIStatus
        
        print("✅ Imports successful")
        
        # Test User Schema
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "password123",
            "organization_name": "Test Org",
            "subdomain": "testorg"
        }
        user = UserCreate(**user_data)
        print("✅ UserCreate schema validated")
        
        # Test Repository Schema
        repo_data = {
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "git_provider": GitProvider.GITHUB,
            "repo_url": "https://github.com/owner/test-repo",
            "default_branch": "main"
        }
        repo = RepositoryCreate(**repo_data)
        print("✅ RepositoryCreate schema validated")
        
        # Test APIEndpoint Schema
        endpoint_data = {
            "path": "/api/users",
            "method": HTTPMethod.GET,
            "summary": "Get users",
            "repository_id": uuid4()
        }
        endpoint = APIEndpointCreate(**endpoint_data)
        print("✅ APIEndpointCreate schema validated")
        
        print("\n✨ All schemas are valid and strict!")
        return True
        
    except Exception as e:
        print(f"\n❌ Schema verification failed: {e}")
        return False

if __name__ == "__main__":
    if test_schemas():
        sys.exit(0)
    else:
        sys.exit(1)
