"""Clean slate - delete all users and orgs, keeping only repos"""
import asyncio
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User, Organization

async def clean_slate():
    async with AsyncSessionLocal() as db:
        # Get all repos for reference
        result = await db.execute(select(Repository))
        repos = result.scalars().all()
        repo_org_ids = {r.organization_id for r in repos}
        
        print(f"Found {len(repos)} repositories")
        print(f"Unique org IDs in repos: {repo_org_ids}")
        
        # Delete ALL users
        await db.execute(delete(User))
        print("Deleted all users")
        
        # Keep only organizations that have repos
        result = await db.execute(select(Organization))
        orgs = result.scalars().all()
        
        for org in orgs:
            if org.id not in repo_org_ids:
                await db.delete(org)
                print(f"Deleted unused org: {org.name} ({org.id})")
            else:
                print(f"Keeping org with repos: {org.name} ({org.id})")
        
        await db.commit()
        print("\n✅ Clean slate complete!")
        print("Next API call will create fresh dev user with correct org")

if __name__ == "__main__":
    asyncio.run(clean_slate())
