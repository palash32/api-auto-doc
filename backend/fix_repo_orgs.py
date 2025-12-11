"""Fix repository organization IDs to match dev user"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User

async def fix_repo_org_ids():
    async with AsyncSessionLocal() as db:
        # Get dev user
        result = await db.execute(select(User).where(User.email == "dev@test.com"))
        dev_user = result.scalar_one_or_none()
        
        if not dev_user:
            print("ERROR: Dev user not found!")
            return
        
        print(f"Dev User: {dev_user.email}")
        print(f"  User ID: {dev_user.id}")
        print(f"  Org ID:  {dev_user.organization_id}")
        print()
        
        # Get all repositories
        result = await db.execute(select(Repository))
        all_repos = result.scalars().all()
        
        print(f"Total Repositories: {len(all_repos)}")
        print()
        
        # Update repos that don't belong to dev org
        updated_count = 0
        for repo in all_repos:
            if repo.organization_id != dev_user.organization_id:
                print(f"Updating: {repo.full_name}")
                print(f"  Old Org ID: {repo.organization_id}")
                print(f"  New Org ID: {dev_user.organization_id}")
                repo.organization_id = dev_user.organization_id
                updated_count += 1
        
        if updated_count > 0:
            await db.commit()
            print(f"\nUpdated {updated_count} repositories")
        else:
            print("All repositories already have correct org ID")
        
        # Verify
        result = await db.execute(
            select(Repository).where(Repository.organization_id == dev_user.organization_id)
        )
        dev_repos = result.scalars().all()
        print(f"\nRepositories for dev user's org: {len(dev_repos)}")
        for repo in dev_repos:
            print(f"  - {repo.full_name}")

if __name__ == "__main__":
    asyncio.run(fix_repo_org_ids())
