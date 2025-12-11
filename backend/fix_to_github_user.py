"""Assign all repositories to the GitHub authenticated user's organization"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User

async def fix_repo_assignments():
    async with AsyncSessionLocal() as session:
        # Find the GitHub user (palash32)
        result = await session.execute(
            select(User).where(User.email.like('%palash32%'))
        )
        github_user = result.scalar_one_or_none()
        
        if not github_user:
            print("GitHub user not found! Listing all users:")
            result = await session.execute(select(User))
            all_users = result.scalars().all()
            for user in all_users:
                print(f"  - {user.email} (ID: {user.id}, Org: {user.organization_id})")
            return
        
        print(f"\nFound GitHub user: {github_user.email}")
        print(f"  User ID: {github_user.id}")
        print(f"  Org ID: {github_user.organization_id}\n")
        
        # Get all repositories
        result = await session.execute(select(Repository))
        repos = result.scalars().all()
        
        print(f"Updating {len(repos)} repositories to use org ID: {github_user.organization_id}\n")
        
        updated = 0
        for repo in repos:
            if repo.organization_id != github_user.organization_id:
                print(f"  Updating: {repo.full_name}")
                repo.organization_id = github_user.organization_id
                updated += 1
            else:
                print(f"  Already correct: {repo.full_name}")
        
        if updated > 0:
            await session.commit()
            print(f"\nUpdated {updated} repositories successfully!")
        else:
            print("\nAll repositories already assigned correctly!")

if __name__ == "__main__":
    asyncio.run(fix_repo_assignments())
