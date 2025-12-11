import asyncio
import uuid
import logging
from app.services.scan_service import ScanService
from app.models.repository import Repository, GitProvider, ScanStatus
from app.models.user import Organization, SubscriptionTier
from app.core.database import AsyncSessionLocal, async_engine, Base

# Suppress SQLAlchemy logs
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

# Use a valid public repo for testing
TEST_REPO_URL = "https://github.com/encode/starlette"
TEST_REPO_NAME = "encode/starlette"

async def verify_pipeline():
    print("🚀 Starting Pipeline Verification...")
    
    # 1. Setup DB Data
    async with AsyncSessionLocal() as db:
        # Check if Org exists
        from sqlalchemy import select
        result = await db.execute(select(Organization).where(Organization.name == "Test Org"))
        org = result.scalar_one_or_none()
        
        if not org:
            org = Organization(
                name="Test Org",
                subdomain="test-org",
                subscription_tier=SubscriptionTier.FREE
            )
            db.add(org)
            await db.flush()
        
        # Check if Repo exists
        result = await db.execute(select(Repository).where(Repository.full_name == TEST_REPO_NAME))
        repo = result.scalar_one_or_none()
        
        if not repo:
            repo = Repository(
                organization_id=org.id,
                name="fastapi-hello-world",
                full_name=TEST_REPO_NAME,
                git_provider=GitProvider.GITHUB,
                repo_url=TEST_REPO_URL,
                scan_status=ScanStatus.PENDING
            )
            db.add(repo)
            await db.commit()
            await db.refresh(repo)
        else:
            # Reset status
            repo.scan_status = ScanStatus.PENDING
            await db.commit()
            
        repo_id = repo.id
        print(f"✅ Using Test Repo: {repo_id}")

    # 2. Run Scan Service
    print("\n🔄 Running ScanService...")
    
    # Mock AI Service to return fake docs
    from unittest.mock import MagicMock
    
    service = ScanService()
    
    # Create a fake async method
    async def mock_generate(*args, **kwargs):
        return {
            "summary": "Mocked Endpoint",
            "description": "This is a mocked endpoint for testing.",
            "method": "GET",
            "path": "/mocked/path",
            "tags": ["test"],
            "auth_required": False
        }
        
    service.ai_service.generate_doc = MagicMock(side_effect=mock_generate)
    
    await service.process_repository(repo_id)
    
    # 3. Verify Results
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from app.models.api_endpoint import APIEndpoint
        
        # Check Repo Status
        result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = result.scalar_one()
        print(f"\n📊 Repo Status: {repo.scan_status}")
        print(f"   Last Scanned: {repo.last_scanned}")
        print(f"   API Count: {repo.api_count}")
        if repo.scan_error_message:
            print(f"   ❌ Error: {repo.scan_error_message}")
        
        if repo.scan_status == ScanStatus.COMPLETED:
            print("✅ Scan marked as COMPLETED")
        else:
            print(f"❌ Scan failed")
            
        # Check Endpoints
        result = await db.execute(select(APIEndpoint).where(APIEndpoint.repository_id == repo_id))
        endpoints = result.scalars().all()
        print(f"\nFound {len(endpoints)} endpoints in DB:")
        
        for ep in endpoints:
            print(f" - {ep.method} {ep.path} ({ep.summary})")
            
        if len(endpoints) > 0:
            print("✅ Endpoints successfully discovered and saved!")
        else:
            print("⚠️ No endpoints found (might be expected if repo has no APIs or AI failed)")

if __name__ == "__main__":
    # Ensure tables exist
    async def init_db():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    asyncio.run(init_db())
    asyncio.run(verify_pipeline())
