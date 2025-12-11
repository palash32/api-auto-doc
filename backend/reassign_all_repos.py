"""Reassign all repos to current dev user's organization"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User

async def reassign_repos_to_dev_org():
    async with AsyncSessionLocal() as db:
        # Get dev user
        result = await db.execute(select(User).where(User.email == "dev@test.com"))
        dev_user = result.scalar_one_or_none()
        
        if not dev_user:
            print("ERROR: Dev user not found!")
            return
        
        print(f"Dev User Organization ID: {dev_user.organization_id}")
        
        # Get ALL repositories
        result = await db.execute(select(Repository))
        all_repos = result.scalars().all()
        
        print(f"\nTotal Repositories: {len(all_repos)}")
        
        # Reassign ALL repos to dev user's org
        updated = 0
        for repo in all_repos:
            if repo.organization_id != dev_user.organization_id:
                print(f"  Reassigning: {repo.full_name}")
                print(f"    From org:  {repo.organization_id}")
                print(f"    To org:    {dev_user.organization_id}")
                repo.organization_id = dev_user.organization_id
                updated += 1
            else:
                print(f"  OK: {repo.full_name} already assigned to dev org")
        
        if updated > 0:
            await db.commit()
            print(f"\n✅ Reassigned {updated} repositories")
        else:
            print(f"\n✅ All {len(all_repos)} repositories already assigned correctly")

if __name__ == "__main__":
    asyncio.run(reassign_repos_to_dev_org())
