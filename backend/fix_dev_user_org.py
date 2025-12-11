"""Fix dev user to use the correct organization with repos"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User, Organization

async def fix_dev_user_org():
    async with AsyncSessionLocal() as db:
        # Find the organization that has repositories
        result = await db.execute(select(Repository))
        repos = result.scalars().all()
        
        if not repos:
            print("No repositories found!")
            return
        
        # Get the org_id from the first repo (they should all be the same)
        correct_org_id = repos[0].organization_id
        print(f"Found {len(repos)} repositories with org_id: {correct_org_id}")
        
        # Get dev user
        result = await db.execute(select(User).where(User.email == "dev@test.com"))
        dev_user = result.scalar_one_or_none()
        
        if not dev_user:
            print("Dev user not found!")
            return
        
        print(f"\nDev user current org_id: {dev_user.organization_id}")
        
        if dev_user.organization_id != correct_org_id:
            print(f"MISMATCH! Updating dev user org_id to: {correct_org_id}")
            dev_user.organization_id = correct_org_id
            await db.commit()
            print("✅ Dev user organization updated!")
            
            # Delete unnecessary organizations
            result = await db.execute(select(Organization))
            all_orgs = result.scalars().all()
            
            for org in all_orgs:
                # Check if any users belong to this org
                result2 = await db.execute(select(User).where(User.organization_id == org.id))
                users = result2.scalars().all()
                
                # Check if any repos belong to this org
                result3 = await db.execute(select(Repository).where(Repository.organization_id == org.id))
                org_repos = result3.scalars().all()
                
                if len(users) == 0 and len(org_repos) == 0:
                    print(f"Deleting unused organization: {org.name} ({org.id})")
                    await db.delete(org)
            
            await db.commit()
        else:
            print("✅ Dev user already has correct org_id")

if __name__ == "__main__":
    asyncio.run(fix_dev_user_org())
