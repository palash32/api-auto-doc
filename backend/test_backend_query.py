"""Test the backend API endpoint directly"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from uuid import UUID
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository

# The user ID from the token
USER_ID = "813729b9-d880-44d5-b460-a3b998e2c9f0"

async def test_backend_query():
    async with AsyncSessionLocal() as session:
        # Simulate what the backend does
        user_id = UUID(USER_ID)
        
        print(f"Testing backend query with user_id: {user_id}\n")
        
        # This is exactly what the backend endpoint does
        result = await session.execute(
            select(Repository).where(Repository.organization_id == user_id)
        )
        repos = result.scalars().all()
        
        print(f"Query returned: {len(repos)} repositories\n")
        
        for repo in repos:
            print(f"  - {repo.full_name}")
        
        if len(repos) == 0:
            # Check if user_id type matches
            print("\nDEBUG: Checking organization_id types...")
            all_result = await session.execute(select(Repository))
            all_repos = all_result.scalars().all()
            for repo in all_repos:
                print(f"  {repo.full_name}: org_id={repo.organization_id} (type={type(repo.organization_id).__name__})")

if __name__ == "__main__":
    asyncio.run(test_backend_query())
