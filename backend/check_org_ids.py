"""Check organization IDs for all repos and users"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User, Organization
from uuid import UUID

async def check_org_ids():
    async with AsyncSessionLocal() as db:
        # Get all users
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print("USERS:\n" + "="*60)
        for user in users:
            print(f"Email: {user.email}")
            print(f"  User ID: {user.id}")
            print(f"  Org ID:  {user.organization_id}")
            print()
        
        # Get all orgs
        result = await db.execute(select(Organization))
        orgs = result.scalars().all()
        
        print("\nORGANIZATIONS:\n" + "="*60)
        for org in orgs:
            print(f"Name: {org.name}")
            print(f"  Org ID: {org.id}")
            print()
        
        # Get all repos
        result = await db.execute(select(Repository))
        repos = result.scalars().all()
        
        print("\nREPOSITORIES:\n" + "="*60)
        for repo in repos:
            print(f"{repo.full_name}")
            print(f"  Repo ID: {repo.id}")
            print(f"  Org ID:  {repo.organization_id}")
            
            # Find which org this belongs to
            result2 = await db.execute(select(Organization).where(Organization.id == repo.organization_id))
            org = result2.scalar_one_or_none()
            if org:
                print(f"  Org Name: {org.name}")
            else:
                print(f"  Org Name: NOT FOUND!")
            print()
        
        # Summary
        print("\nSUMMARY:\n" + "="*60)
        print(f"Total Users: {len(users)}")
        print(f"Total Organizations: {len(orgs)}")
        print(f"Total Repositories: {len(repos)}")
        
        # Check for orphaned repos
        org_ids = {org.id for org in orgs}
        for repo in repos:
            if repo.organization_id not in org_ids:
                print(f"\nWARNING: Repo '{repo.full_name}' has invalid org_id: {repo.organization_id}")

if __name__ == "__main__":
    asyncio.run(check_org_ids())
