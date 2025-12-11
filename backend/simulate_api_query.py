"""Simulate the exact API query"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User
from uuid import UUID

async def simulate_api_query():
    async with AsyncSessionLocal() as db:
        # Simulate get_current_user_optional for dev mode
        test_email = "dev@test.com"
        result = await db.execute(select(User).where(User.email == test_email))
        user = result.scalar_one_or_none()
        
        if not user:
            print("ERROR: Dev user not found!")
            return
        
        print("=" * 70)
        print("SIMULATING API CALL TO /api/repositories/")
        print("=" * 70)
        print(f"\nUser from get_current_user_optional:")
        print(f"  Email: {user.email}")
        print(f"  User ID: {user.id}")
        print(f"  Org ID: {user.organization_id}")
        
        # This is what the API does
        current_user = {
            "sub": str(user.id),
            "id": str(user.id),
            "email": user.email,
            "organization_id": str(user.organization_id)
        }
        
        print(f"\ncurrent_user dict:")
        print(f"  {current_user}")
        
        # The actual query
        org_id = UUID(current_user["organization_id"])
        print(f"\nQuerying with org_id: {org_id}")
        
        result = await db.execute(
            select(Repository).where(Repository.organization_id == org_id)
        )
        repos = result.scalars().all()
        
        print(f"\nQuery Results:")
        print(f"  Found {len(repos)} repositories")
        for repo in repos:
            print(f"    - {repo.full_name} (org_id: {repo.organization_id})")

if __name__ == "__main__":
    asyncio.run(simulate_api_query())
