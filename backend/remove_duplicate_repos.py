"""Remove duplicate repositories, keeping only one of each"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository

async def remove_duplicates():
    async with AsyncSessionLocal() as session:
        # Get all repositories
        result = await session.execute(select(Repository).order_by(Repository.created_at))
        all_repos = result.scalars().all()
        
        print(f"\n=== Found {len(all_repos)} total repositories ===\n")
        
        # Track seen full_names
        seen = set()
        to_delete = []
        
        for repo in all_repos:
            if repo.full_name in seen:
                print(f"DUPLICATE: {repo.full_name} (ID: {repo.id})")
                to_delete.append(repo)
            else:
                print(f"KEEP: {repo.full_name} (ID: {repo.id})")
                seen.add(repo.full_name)
        
        if to_delete:
            print(f"\n=== Deleting {len(to_delete)} duplicates ===")
            for repo in to_delete:
                await session.delete(repo)
            await session.commit()
            print(f"Deleted {len(to_delete)} duplicate repositories")
        else:
            print("\nNo duplicates found")
        
        print(f"\nRemaining repositories: {len(seen)}")

if __name__ == "__main__":
    asyncio.run(remove_duplicates())
