"""Check for duplicate users/orgs"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User, Organization

async def check_duplicates():
    async with AsyncSessionLocal() as db:
        # Get all users
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print(f"TOTAL USERS: {len(users)}")
        for i, user in enumerate(users, 1):
            print(f"\n{i}. {user.email}")
            print(f"   User ID: {user.id}")
            print(f"   Org ID:  {user.organization_id}")
        
        # Get all orgs
        result = await db.execute(select(Organization))
        orgs = result.scalars().all()
        
        print(f"\n\nTOTAL ORGANIZATIONS: {len(orgs)}")
        for i, org in enumerate(orgs, 1):
            print(f"\n{i}. {org.name}")
            print(f"   Org ID: {org.id}")
        
        # Get all repos
        result = await db.execute(select(Repository))
        repos = result.scalars().all()
        
        print(f"\n\nTOTAL REPOSITORIES: {len(repos)}")
        
        # Group repos by org_id
        repos_by_org = {}
        for repo in repos:
            if repo.organization_id not in repos_by_org:
                repos_by_org[repo.organization_id] = []
            repos_by_org[repo.organization_id].append(repo)
        
        print("\nREPOSITORIES BY ORGANIZATION:")
        for org_id, org_repos in repos_by_org.items():
            # Find org name
            result2 = await db.execute(select(Organization).where(Organization.id == org_id))
            org = result2.scalar_one_or_none()
            org_name = org.name if org else "UNKNOWN"
            
            print(f"\n  {org_name} ({org_id}):")
            print(f"  Count: {len(org_repos)}")
            for repo in org_repos:
                print(f"    - {repo.full_name}")

if __name__ == "__main__":
    asyncio.run(check_duplicates())
