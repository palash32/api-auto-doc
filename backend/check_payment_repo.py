"""Check if Payment_Gateway_Integration repository exists in database"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from sqlalchemy import select, text
from app.core.database import async_engine, AsyncSessionLocal
from app.models.repository import Repository

async def check_repo():
    async with AsyncSessionLocal() as session:
        # Check for Payment_Gateway_Integration
        result = await session.execute(
            select(Repository).where(Repository.full_name.like('%Payment_Gateway_Integration%'))
        )
        payment_repo = result.scalar_one_or_none()
        
        if payment_repo:
            print(f"\nFOUND: {payment_repo.full_name}")
            print(f"   ID: {payment_repo.id}")
            print(f"   Status: {payment_repo.scan_status}")
            print(f"   Org ID: {payment_repo.organization_id}")
        else:
            print("\nNOT FOUND: Payment_Gateway_Integration not in database")
        
        # List all repos
        result = await session.execute(select(Repository))
        all_repos = result.scalars().all()
        print(f"\n--- All {len(all_repos)} repositories ---")
        for repo in all_repos:
            print(f"  - {repo.full_name} (org: {repo.organization_id})")

if __name__ == "__main__":
    asyncio.run(check_repo())
