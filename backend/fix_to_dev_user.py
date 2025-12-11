"""Assign all repositories to the dev user's organization"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User

async def fix_to_dev_user():
    async with AsyncSessionLocal() as session:
        # Get the dev/test user
        test_email = "dev@test.com"
        result = await session.execute(select(User).where(User.email == test_email))
        dev_user = result.scalar_one_or_none()
        
        if not dev_user:
            print("ERROR: Dev user not found!")
            return
        
        print(f"\nDev user found: {dev_user.email}")
        print(f"  User ID: {dev_user.id}")
        print(f"  Org ID: {dev_user.organization_id}\n")
        
        # Get all repositories
        result = await session.execute(select(Repository))
        repos = result.scalars().all()
        
        print(f"Updating {len(repos)} repositories to dev user's org...\n")
        
        updated = 0
        for repo in repos:
            if repo.organization_id != dev_user.organization_id:
                print(f"  Updating: {repo.full_name}")
                repo.organization_id = dev_user.organization_id
                updated += 1
            else:
                print(f"  Already correct: {repo.full_name}")
        
        if updated > 0:
            await session.commit()
            print(f"\nSUCCESS: Updated {updated} repositories to dev user's organization!")
            print(f"Repositories should now appear in dashboard.")
        else:
            print("\nAll repositories already assigned correctly!")

if __name__ == "__main__":
    asyncio.run(fix_to_dev_user())
