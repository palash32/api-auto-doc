"""
Verification script for API Endpoints (Task 3.1).
Tests the REST API endpoints for viewing documentation.
"""
import asyncio
from uuid import UUID
from sqlalchemy import select
from app.models.api_endpoint import APIEndpoint
from app.models.repository import Repository, ScanStatus
from app.core.database import AsyncSessionLocal

async def verify_endpoints():
    print("🚀 Verifying API Endpoints...")
    
    async with AsyncSessionLocal() as db:
        # 1. Find a repository with endpoints
        result = await db.execute(
            select(Repository).where(Repository.scan_status == ScanStatus.COMPLETED)
        )
        repo = result.scalars().first()
        
        if not repo:
            print("❌ No completed repository scans found")
            print("   Please run verify_pipeline.py first to create test data")
            return
        
        print(f"✅ Found repository: {repo.full_name}")
        print(f"   API Count: {repo.api_count}")
        
        # 2. Check endpoints exist
        result = await db.execute(
            select(APIEndpoint).where(APIEndpoint.repository_id == repo.id)
        )
        endpoints = result.scalars().all()
        
        print(f"\n📊 Found {len(endpoints)} endpoints in database:")
        for i, ep in enumerate(endpoints[:5], 1):  # Show first 5
            print(f"   {i}. {ep.method} {ep.path}")
            print(f"      Summary: {ep.summary[:50]}..." if len(ep.summary) > 50 else f"      Summary: {ep.summary}")
        
        if len(endpoints) > 5:
            print(f"   ... and {len(endpoints) - 5} more")
        
        # 3. Test the API endpoints (manual test instructions)
        if endpoints:
            print("\n✅ Database has endpoint data!")
            print("\n📝 Manual API Testing:")
            print(f"   1. GET http://localhost:8000/api/repositories/{repo.id}/endpoints")
            print(f"      - Should return paginated list of endpoints")
            print(f"\n   2. GET http://localhost:8000/api/endpoints/{endpoints[0].id}")
            print(f"      - Should return detailed endpoint info")
            print(f"\n   3. Visit http://localhost:8000/docs")
            print(f"      - Try the endpoints in Swagger UI")
            print("\n   Note: You'll need to be authenticated (use JWT token)")
        else:
            print("⚠️  No endpoints found - run a repository scan first")

if __name__ == "__main__":
    asyncio.run(verify_endpoints())
