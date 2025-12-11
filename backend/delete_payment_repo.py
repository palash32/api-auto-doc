"""Delete Payment_Gateway_Integration repository from database"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository

async def delete_payment_repo():
    async with AsyncSessionLocal() as session:
        # Find the repository
        result = await session.execute(
            select(Repository).where(Repository.full_name == 'palash32/Payment_Gateway_Integration')
        )
        repo = result.scalar_one_or_none()
        
        if repo:
            print(f"Found repository: {repo.full_name}")
            print(f"  ID: {repo.id}")
            print(f"  Org ID: {repo.organization_id}")
            print(f"  Status: {repo.scan_status}")
            
            # Delete it
            await session.delete(repo)
            await session.commit()
            print(f"\nDeleted repository: {repo.full_name}")
        else:
            print("Repository palash32/Payment_Gateway_Integration not found.")

if __name__ == "__main__":
    asyncio.run(delete_payment_repo())
