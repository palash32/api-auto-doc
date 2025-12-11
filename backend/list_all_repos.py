"""List all repositories and their organization IDs"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User

async def list_repos_and_users():
    async with AsyncSessionLocal() as session:
        # Get all users
        user_result = await session.execute(select(User))
        users = user_result.scalars().all()
        
        print("\n=== USERS ===")
        for user in users:
            print(f"{user.email}")
            print(f"  User ID: {user.id}")
            print(f"  Org ID: {user.organization_id}")
            print()
        
        # Get all repositories
        repo_result = await session.execute(select(Repository))
        repos = repo_result.scalars().all()
        
        print(f"\n=== REPOSITORIES (Total: {len(repos)}) ===")
        for repo in repos:
            print(f"{repo.full_name}")
            print(f"  Repo ID: {repo.id}")
            print(f"  Org ID: {repo.organization_id}")
            print(f"  Status: {repo.scan_status}")
            print()

if __name__ == "__main__":
    asyncio.run(list_repos_and_users())
