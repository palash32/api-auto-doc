import asyncio
from sqlalchemy import select
from app.core.database import get_async_db
from app.models.repository import Repository

async def list_all_repos():
    async for db in get_async_db():
        result = await db.execute(select(Repository))
        repos = result.scalars().all()
        
        print(f"\n=== Total repositories in database: {len(repos)} ===\n")
        for repo in repos:
            print(f"Repository: {repo.full_name}")
            print(f"  ID: {repo.id}")
            print(f"  Status: {repo.scan_status}")
            print(f"  Organization ID: {repo.organization_id}")
            print(f"  URL: {repo.repo_url}")
            print()

if __name__ == "__main__":
    asyncio.run(list_all_repos())
