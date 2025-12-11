"""Update all repositories to use the current user's organization ID"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from uuid import UUID
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository

# The current user's ID from the JWT token
CURRENT_USER_ID = "813729b9-d880-44d5-b460-a3b998e2c9f0"

async def fix_org_ids():
    async with AsyncSessionLocal() as session:
        # Get all repositories
        result = await session.execute(select(Repository))
        repos = result.scalars().all()
        
        print(f"\n=== Updating {len(repos)} repositories ===\n")
        
        updated_count = 0
        for repo in repos:
            if str(repo.organization_id) != CURRENT_USER_ID:
                print(f"Updating: {repo.full_name}")
                print(f"  Old Org ID: {repo.organization_id}")
                print(f"  New Org ID: {CURRENT_USER_ID}")
                
                repo.organization_id = UUID(CURRENT_USER_ID)
                updated_count += 1
            else:
                print(f"Already correct: {repo.full_name}")
        
        if updated_count > 0:
            await session.commit()
            print(f"\n✓ Updated {updated_count} repositories")
        else:
            print("\n✓ All repositories already have correct organization ID")

if __name__ == "__main__":
    asyncio.run(fix_org_ids())
