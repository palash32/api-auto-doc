"""Check current state of all repositories in database"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository

EXPECTED_USER_ID = "813729b9-d880-44d5-b460-a3b998e2c9f0"

async def check_current_state():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Repository))
        repos = result.scalars().all()
        
        print(f"\nTotal repositories in database: {len(repos)}\n")
        
        matching = 0
        not_matching = 0
        
        for repo in repos:
            org_id_str = str(repo.organization_id)
            matches = org_id_str == EXPECTED_USER_ID
            
            print(f"Repository: {repo.full_name}")
            print(f"  Org ID: {org_id_str}")
            print(f"  Matches current user: {'YES' if matches else 'NO'}")
            print()
            
            if matches:
                matching += 1
            else:
                not_matching += 1
        
        print(f"Summary:")
        print(f"  Matching current user ({EXPECTED_USER_ID}): {matching}")
        print(f"  NOT matching: {not_matching}")

if __name__ == "__main__":
    asyncio.run(check_current_state())
