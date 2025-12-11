"""Debug script to show the exact mismatch"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User
from app.core.config import settings

async def debug_mismatch():
    async with AsyncSessionLocal() as session:
        # Get the test/dev user that backend would use without token
        test_email = "dev@test.com"
        result = await session.execute(select(User).where(User.email == test_email))
        dev_user = result.scalar_one_or_none()
        
        # Get the GitHub user (palash32)
        result = await session.execute(
            select(User).where(User.email.like('%palash32%'))
        )
        github_user = result.scalar_one_or_none()
        
        # Get all repositories
        result = await session.execute(select(Repository))
        repos = result.scalars().all()
        
        print(f"\n=== SETTINGS ===")
        print(f"Is Development Mode: {settings.is_development}")
        print()
        
        print(f"=== DEV/TEST USER (used when no valid token) ===")
        if dev_user:
            print(f"Email: {dev_user.email}")
            print(f"User ID: {dev_user.id}")
            print(f"Org ID: {dev_user.organization_id}")
        else:
            print("Dev user does not exist yet")
        print()
        
        print(f"=== GITHUB USER (palash32) ===")
        if github_user:
            print(f"Email: {github_user.email}")
            print(f"User ID: {github_user.id}")
            print(f"Org ID: {github_user.organization_id}")
        else:
            print("GitHub user not found!")
        print()
        
        print(f"=== ALL REPOSITORIES ({len(repos)}) ===")
        for repo in repos:
            print(f"{repo.full_name}")
            print(f"  Org ID: {repo.organization_id}")
            if dev_user:
                print(f"  Matches dev user: {repo.organization_id == dev_user.organization_id}")
            if github_user:
                print(f"  Matches GitHub user: {repo.organization_id == github_user.organization_id}")
        print()
        
        print(f"=== THE ISSUE ===")
        if dev_user and github_user and dev_user.organization_id != github_user.organization_id:
            print("DEV USER and GITHUB USER have DIFFERENT organization IDs!")
            print("Repositories are assigned to GitHub user's org")
            print("But backend (when no token) uses dev user's org")
            print("This is why API returns [] (empty)")

if __name__ == "__main__":
    asyncio.run(debug_mismatch())
