"""Debug repository visibility issue"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User, Organization

async def debug_repos():
    async with AsyncSessionLocal() as db:
        # Get dev user
        result = await db.execute(select(User).where(User.email == "dev@test.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Dev user not found!")
            return
        
        print(f"\n👤 Dev User:")
        print(f"   Email: {user.email}")
        print(f"   User ID: {user.id}")
        print(f"   Org ID: {user.organization_id}")
        
        # Get organization
        result = await db.execute(select(Organization).where(Organization.id == user.organization_id))
        org = result.scalar_one_or_none()
        
        if org:
            print(f"\n🏢 Organization:")
            print(f"   Name: {org.name}")
            print(f"   ID: {org.id}")
        
        # Get ALL repositories
        result = await db.execute(select(Repository))
        all_repos = result.scalars().all()
        print(f"\n📦 Total Repositories in Database: {len(all_repos)}")
        
        # Get repos for this org
        result = await db.execute(
            select(Repository).where(Repository.organization_id == user.organization_id)
        )
        org_repos = result.scalars().all()
        
        print(f"\n✅ Repositories for Dev User's Org ({user.organization_id}):")
        print(f"   Count: {len(org_repos)}")
        for repo in org_repos:
            print(f"   - {repo.full_name}")
            print(f"     ID: {repo.id}")
            print(f"     Status: {repo.scan_status}")
            print(f"     API Count: {repo.api_count}")
        
        if len(all_repos) != len(org_repos):
            print(f"\n⚠️  Found {len(all_repos) - len(org_repos)} repos with different org_id:")
            other_repos = [r for r in all_repos if r.organization_id != user.organization_id]
            for repo in other_repos:
                print(f"   - {repo.full_name} (org_id: {repo.organization_id})")

if __name__ == "__main__":
    asyncio.run(debug_repos())
