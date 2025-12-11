"""Fix repository organization IDs  - with better output"""
import asyncio
import sys
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
            print("ERROR: Dev user not found!", file=sys.stderr)
            return
        
        print("=" * 70)
        print(f"Dev User: {dev_user.email}")
        print(f"  User ID: {dev_user.id}")
        print(f"  Org ID:  {dev_user.organization_id}")
        print("=" * 70)
        
        # Get all repositories
        result = await db.execute(select(Repository))
        all_repos = result.scalars().all()
        
        print(f"\nTotal Repositories in Database: {len(all_repos)}\n")
        
        # Check and update each repo
        updated_count = 0
        already_correct = 0
        
        for repo in all_repos:
            if repo.organization_id != dev_user.organization_id:
                print(f"[UPDATING] {repo.full_name}")
                print(f"   Old Org ID: {repo.organization_id}")
                print(f"   New Org ID: {dev_user.organization_id}")
                repo.organization_id = dev_user.organization_id
                updated_count += 1
            else:
                print(f"[OK] {repo.full_name} - already has correct org_id")
                already_correct += 1
        
        print("\n" + "=" * 70)
        if updated_count > 0:
            await db.commit()
            print(f"✅ Updated {updated_count} repositories")
        
        print(f"✅ {already_correct} repositories already had correct org_id")
        print("=" * 70)
        
        # Verify
        print("\nVerifying...")
        result = await db.execute(
            select(Repository).where(Repository.organization_id == dev_user.organization_id)
        )
        dev_repos = result.scalars().all()
        print(f"\nRepositories for dev user's org ({dev_user.organization_id}):")
        print(f"Count: {len(dev_repos)}\n")
        for i, repo in enumerate(dev_repos, 1):
            print(f"  {i}. {repo.full_name}")

if __name__ == "__main__":
    asyncio.run(fix_repo_org_ids())
