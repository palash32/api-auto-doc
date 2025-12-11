"""Check what user the backend is actually using"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User

async def check_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"\nTotal users in database: {len(users)}\n")
        
        for user in users:
            print(f"User: {user.email}")
            print(f"  User ID: {user.id}")
            print(f"  Org ID: {user.organization_id}")
            print(f"  Active: {user.is_active}")
            print()

if __name__ == "__main__":
    asyncio.run(check_users())
