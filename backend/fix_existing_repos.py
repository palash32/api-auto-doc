"""Check and fix repository organization IDs if needed"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.user import User

async def check_and_fix_repos():
    async with AsyncSessionLocal() as db:
        # Get all users
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print(f"\n📊 Found {len(users)} users:")
        for user in users:
            print(f"  User: {user.email}")
            print(f"    - User ID: {user.id}")
            print(f"    - Org ID:  {user.organization_id}")
            
            # Find repos with this user's ID as org_id
            result = await db.execute(
                select(Repository).where(Repository.organization_id == user.id)
            )
            wrong_repos = result.scalars().all()
            
            if wrong_repos:
                print(f"    ⚠️  Found {len(wrong_repos)} repos with user_id as org_id (WRONG)")
                for repo in wrong_repos:
                    print(f"       - {repo.full_name} (fixing org_id to {user.organization_id})")
                    repo.organization_id = user.organization_id
                await db.commit()
                print(f"    ✅ Fixed {len(wrong_repos)} repositories")
            
            # Check repos with correct org_id
            result = await db.execute(
                select(Repository).where(Repository.organization_id == user.organization_id)
            )
            correct_repos = result.scalars().all()
            print(f"    ✅ {len(correct_repos)} repos with correct organization_id")
            for repo in correct_repos:
                print(f"       - {repo.full_name}")

if __name__ == "__main__":
    asyncio.run(check_and_fix_repos())
