import asyncio
from sqlalchemy import select
from app.models.repository import Repository
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Repository).where(Repository.full_name == "fastapi/fastapi-hello-world"))
        repo = result.scalar_one_or_none()
        if repo:
            print(f"Status: {repo.scan_status}")
            print(f"Error: {repo.scan_error_message}")
            print(f"API Count: {repo.api_count}")
        else:
            print("Repo not found")

if __name__ == "__main__":
    asyncio.run(check())
