from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.core.database import get_async_db
from app.models.repository import Repository, GitProvider, ScanStatus
from app.models.user import User
from app.api.dev_auth import get_current_user_optional
from app.services.scan_service import ScanService

router = APIRouter()
scan_service = ScanService()


@router.get("/debug", response_model=dict)
async def debug_auth(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Debug endpoint to check current_user data."""
    # Count repos for this org
    org_id = UUID(current_user["organization_id"])
    result = await db.execute(
        select(Repository).where(Repository.organization_id == org_id)
    )
    repos = result.scalars().all()
    
    return {
        "current_user": current_user,
        "organization_id": str(org_id),
        "repo_count": len(repos),
        "repos": [r.full_name for r in repos]
    }



@router.post("/", response_model=dict)
async def create_repository(
    url: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Add a new repository and trigger a scan.
    """
    # Simple parsing for MVP (assuming GitHub)
    if "github.com" not in url:
        raise HTTPException(status_code=400, detail="Only GitHub URLs are supported for now")
    
    parts = url.rstrip("/").split("/")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
        
    owner = parts[-2]
    repo_name = parts[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
        
    full_name = f"{owner}/{repo_name}"

    # Check if exists
    result = await db.execute(select(Repository).where(Repository.full_name == full_name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Repository already exists")

    # Create Repository
    # Use the user's organization ID from the current_user context
    org_id = UUID(current_user["organization_id"])
    
    repo = Repository(
        organization_id=org_id,
        name=repo_name,
        full_name=full_name,
        git_provider=GitProvider.GITHUB,
        repo_url=url,
        scan_status=ScanStatus.PENDING
    )
    
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    # Trigger Background Scan
    background_tasks.add_task(scan_service.process_repository, repo.id)

    return {
        "id": str(repo.id),
        "name": repo.name,
        "full_name": repo.full_name,
        "status": "pending",
        "message": "Repository added and scan started"
    }


@router.get("/", response_model=List[dict])
async def get_repositories(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all repositories for the user's organization."""
    # Use organization_id, not user_id
    org_id = UUID(current_user["organization_id"])
    
    result = await db.execute(
        select(Repository).where(Repository.organization_id == org_id)
    )
    repos = result.scalars().all()
    
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "full_name": r.full_name,
            "url": r.repo_url,
            "status": r.scan_status,
            "api_count": r.api_count,
            "last_scanned": r.last_scanned,
            "health_score": 100 # Placeholder for MVP
        }
        for r in repos
    ]


@router.post("/{repo_id}/scan")
async def rescan_repository(
    repo_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Trigger a manual re-scan."""
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    # Update status
    repo.scan_status = ScanStatus.PENDING
    await db.commit()
    
    # Trigger Scan
    background_tasks.add_task(scan_service.process_repository, repo.id)
    
    return {"message": "Scan started"}
