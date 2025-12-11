"""Version history and changelog API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4
import json

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.version_history import APIVersion, EndpointChange, Changelog, VersionBookmark
from app.models.api_endpoint import APIEndpoint
from app.models.repository import Repository

router = APIRouter()


# ==================== Pydantic Schemas ====================

class VersionCreate(BaseModel):
    version: str
    title: Optional[str] = None
    description: Optional[str] = None
    commit_hash: Optional[str] = None
    commit_message: Optional[str] = None
    branch: Optional[str] = None


class VersionResponse(BaseModel):
    id: str
    repository_id: str
    version: str
    version_number: int
    commit_hash: Optional[str]
    commit_message: Optional[str]
    branch: Optional[str]
    title: Optional[str]
    total_endpoints: int
    added_endpoints: int
    modified_endpoints: int
    removed_endpoints: int
    is_published: bool
    is_latest: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class EndpointChangeResponse(BaseModel):
    id: str
    change_type: str
    path: str
    method: str
    field_changed: Optional[str]
    old_value: Any
    new_value: Any
    is_breaking: bool
    severity: str
    description: Optional[str]


class ChangelogResponse(BaseModel):
    id: str
    version_id: str
    content_markdown: Optional[str]
    breaking_changes: Optional[List[dict]]
    new_endpoints: Optional[List[dict]]
    modified_endpoints: Optional[List[dict]]
    deprecated_endpoints: Optional[List[dict]]
    removed_endpoints: Optional[List[dict]]
    is_published: bool


class VersionDiffResponse(BaseModel):
    from_version: str
    to_version: str
    added: List[dict]
    modified: List[dict]
    removed: List[dict]
    breaking_changes: List[dict]


# ==================== Version Endpoints ====================

@router.get("/repositories/{repository_id}/versions", response_model=List[VersionResponse])
async def list_versions(
    repository_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List all versions for a repository."""
    result = await db.execute(
        select(APIVersion)
        .where(APIVersion.repository_id == repository_id)
        .order_by(desc(APIVersion.version_number))
        .limit(limit)
    )
    versions = result.scalars().all()
    
    return [VersionResponse(
        id=str(v.id),
        repository_id=str(v.repository_id),
        version=v.version,
        version_number=v.version_number,
        commit_hash=v.commit_hash,
        commit_message=v.commit_message,
        branch=v.branch,
        title=v.title,
        total_endpoints=v.total_endpoints,
        added_endpoints=v.added_endpoints,
        modified_endpoints=v.modified_endpoints,
        removed_endpoints=v.removed_endpoints,
        is_published=v.is_published,
        is_latest=v.is_latest,
        created_at=v.created_at
    ) for v in versions]


@router.post("/repositories/{repository_id}/versions", response_model=VersionResponse)
async def create_version(
    repository_id: str,
    data: VersionCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new version snapshot."""
    # Get latest version number
    result = await db.execute(
        select(func.max(APIVersion.version_number))
        .where(APIVersion.repository_id == repository_id)
    )
    max_version = result.scalar() or 0
    
    # Get current endpoints for snapshot
    endpoints_result = await db.execute(
        select(APIEndpoint).where(APIEndpoint.repository_id == repository_id)
    )
    endpoints = endpoints_result.scalars().all()
    
    # Create endpoint snapshot
    endpoints_snapshot = [
        {
            "id": str(e.id),
            "path": e.path,
            "method": e.method,
            "description": e.description,
            "parameters": e.parameters,
            "request_body": e.request_body,
            "response": e.response_example
        }
        for e in endpoints
    ]
    
    # Unmark previous latest
    await db.execute(
        select(APIVersion)
        .where(
            APIVersion.repository_id == repository_id,
            APIVersion.is_latest == True
        )
    )
    
    # Create new version
    version = APIVersion(
        repository_id=repository_id,
        version=data.version,
        version_number=max_version + 1,
        commit_hash=data.commit_hash,
        commit_message=data.commit_message,
        branch=data.branch,
        title=data.title,
        description=data.description,
        endpoints_snapshot=endpoints_snapshot,
        total_endpoints=len(endpoints),
        is_latest=True,
        created_by_id=current_user.get("id")
    )
    
    db.add(version)
    
    # Calculate changes if there's a previous version
    if max_version > 0:
        prev_result = await db.execute(
            select(APIVersion)
            .where(
                APIVersion.repository_id == repository_id,
                APIVersion.version_number == max_version
            )
        )
        prev_version = prev_result.scalar_one_or_none()
        
        if prev_version and prev_version.endpoints_snapshot:
            changes = await _calculate_changes(
                prev_version.endpoints_snapshot,
                endpoints_snapshot,
                version
            )
            version.added_endpoints = changes["added"]
            version.modified_endpoints = changes["modified"]
            version.removed_endpoints = changes["removed"]
            
            for change in changes["changes"]:
                db.add(change)
    
    await db.commit()
    await db.refresh(version)
    
    return VersionResponse(
        id=str(version.id),
        repository_id=str(version.repository_id),
        version=version.version,
        version_number=version.version_number,
        commit_hash=version.commit_hash,
        commit_message=version.commit_message,
        branch=version.branch,
        title=version.title,
        total_endpoints=version.total_endpoints,
        added_endpoints=version.added_endpoints,
        modified_endpoints=version.modified_endpoints,
        removed_endpoints=version.removed_endpoints,
        is_published=version.is_published,
        is_latest=version.is_latest,
        created_at=version.created_at
    )


@router.get("/versions/{version_id}", response_model=VersionResponse)
async def get_version(
    version_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific version with its endpoint snapshot."""
    result = await db.execute(
        select(APIVersion).where(APIVersion.id == version_id)
    )
    version = result.scalar_one_or_none()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return VersionResponse(
        id=str(version.id),
        repository_id=str(version.repository_id),
        version=version.version,
        version_number=version.version_number,
        commit_hash=version.commit_hash,
        commit_message=version.commit_message,
        branch=version.branch,
        title=version.title,
        total_endpoints=version.total_endpoints,
        added_endpoints=version.added_endpoints,
        modified_endpoints=version.modified_endpoints,
        removed_endpoints=version.removed_endpoints,
        is_published=version.is_published,
        is_latest=version.is_latest,
        created_at=version.created_at
    )


@router.get("/versions/{version_id}/endpoints")
async def get_version_endpoints(
    version_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get endpoints snapshot for a specific version (time-travel)."""
    result = await db.execute(
        select(APIVersion).where(APIVersion.id == version_id)
    )
    version = result.scalar_one_or_none()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return {
        "version": version.version,
        "version_number": version.version_number,
        "endpoints": version.endpoints_snapshot or []
    }


# ==================== Diff Endpoints ====================

@router.get("/versions/{version_id}/changes", response_model=List[EndpointChangeResponse])
async def get_version_changes(
    version_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all changes in a specific version."""
    result = await db.execute(
        select(EndpointChange)
        .where(EndpointChange.version_id == version_id)
        .order_by(EndpointChange.is_breaking.desc())
    )
    changes = result.scalars().all()
    
    return [
        EndpointChangeResponse(
            id=str(c.id),
            change_type=c.change_type,
            path=c.path,
            method=c.method,
            field_changed=c.field_changed,
            old_value=c.old_value,
            new_value=c.new_value,
            is_breaking=c.is_breaking,
            severity=c.severity,
            description=c.description
        )
        for c in changes
    ]


@router.get("/diff/{from_version_id}/{to_version_id}", response_model=VersionDiffResponse)
async def compare_versions(
    from_version_id: str,
    to_version_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Compare two versions and get detailed diff."""
    # Get both versions
    from_result = await db.execute(
        select(APIVersion).where(APIVersion.id == from_version_id)
    )
    from_version = from_result.scalar_one_or_none()
    
    to_result = await db.execute(
        select(APIVersion).where(APIVersion.id == to_version_id)
    )
    to_version = to_result.scalar_one_or_none()
    
    if not from_version or not to_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    from_endpoints = {f"{e['method']}:{e['path']}": e for e in (from_version.endpoints_snapshot or [])}
    to_endpoints = {f"{e['method']}:{e['path']}": e for e in (to_version.endpoints_snapshot or [])}
    
    added = []
    modified = []
    removed = []
    breaking = []
    
    # Find added and modified
    for key, endpoint in to_endpoints.items():
        if key not in from_endpoints:
            added.append(endpoint)
        else:
            # Check for modifications
            old = from_endpoints[key]
            if old.get("description") != endpoint.get("description") or \
               old.get("parameters") != endpoint.get("parameters"):
                modified.append({
                    "endpoint": endpoint,
                    "changes": _get_field_changes(old, endpoint)
                })
    
    # Find removed
    for key, endpoint in from_endpoints.items():
        if key not in to_endpoints:
            removed.append(endpoint)
            breaking.append({
                "type": "endpoint_removed",
                "path": endpoint["path"],
                "method": endpoint["method"],
                "description": f"Endpoint {endpoint['method']} {endpoint['path']} was removed"
            })
    
    return VersionDiffResponse(
        from_version=from_version.version,
        to_version=to_version.version,
        added=added,
        modified=modified,
        removed=removed,
        breaking_changes=breaking
    )


# ==================== Changelog Endpoints ====================

@router.get("/versions/{version_id}/changelog", response_model=ChangelogResponse)
async def get_changelog(
    version_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get or generate changelog for a version."""
    result = await db.execute(
        select(Changelog).where(Changelog.version_id == version_id)
    )
    changelog = result.scalar_one_or_none()
    
    if not changelog:
        # Generate changelog
        changelog = await _generate_changelog(version_id, db)
    
    return ChangelogResponse(
        id=str(changelog.id),
        version_id=str(changelog.version_id),
        content_markdown=changelog.content_markdown,
        breaking_changes=changelog.breaking_changes,
        new_endpoints=changelog.new_endpoints,
        modified_endpoints=changelog.modified_endpoints,
        deprecated_endpoints=changelog.deprecated_endpoints,
        removed_endpoints=changelog.removed_endpoints,
        is_published=changelog.is_published
    )


@router.post("/versions/{version_id}/changelog/publish")
async def publish_changelog(
    version_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Publish a changelog."""
    result = await db.execute(
        select(Changelog).where(Changelog.version_id == version_id)
    )
    changelog = result.scalar_one_or_none()
    
    if not changelog:
        changelog = await _generate_changelog(version_id, db)
    
    changelog.is_published = True
    changelog.published_at = datetime.utcnow()
    
    # Also publish the version
    version_result = await db.execute(
        select(APIVersion).where(APIVersion.id == version_id)
    )
    version = version_result.scalar_one_or_none()
    if version:
        version.is_published = True
    
    await db.commit()
    
    return {"message": "Changelog published"}


# ==================== Helper Functions ====================

async def _calculate_changes(old_endpoints: List[dict], new_endpoints: List[dict], version: APIVersion) -> dict:
    """Calculate changes between two endpoint snapshots."""
    old_map = {f"{e['method']}:{e['path']}": e for e in old_endpoints}
    new_map = {f"{e['method']}:{e['path']}": e for e in new_endpoints}
    
    changes = []
    added = 0
    modified = 0
    removed = 0
    
    # Find added and modified
    for key, endpoint in new_map.items():
        if key not in old_map:
            added += 1
            changes.append(EndpointChange(
                version_id=str(version.id),
                change_type="added",
                path=endpoint["path"],
                method=endpoint["method"],
                description=f"Added endpoint {endpoint['method']} {endpoint['path']}"
            ))
        else:
            old = old_map[key]
            if old.get("description") != endpoint.get("description"):
                modified += 1
                changes.append(EndpointChange(
                    version_id=str(version.id),
                    change_type="modified",
                    path=endpoint["path"],
                    method=endpoint["method"],
                    field_changed="description",
                    old_value=old.get("description"),
                    new_value=endpoint.get("description"),
                    description=f"Modified description for {endpoint['method']} {endpoint['path']}"
                ))
    
    # Find removed
    for key, endpoint in old_map.items():
        if key not in new_map:
            removed += 1
            changes.append(EndpointChange(
                version_id=str(version.id),
                change_type="removed",
                path=endpoint["path"],
                method=endpoint["method"],
                is_breaking=True,
                severity="high",
                description=f"Removed endpoint {endpoint['method']} {endpoint['path']}"
            ))
    
    return {
        "added": added,
        "modified": modified,
        "removed": removed,
        "changes": changes
    }


def _get_field_changes(old: dict, new: dict) -> List[dict]:
    """Get list of field changes between two endpoint snapshots."""
    changes = []
    fields = ["description", "parameters", "request_body", "response"]
    
    for field in fields:
        if old.get(field) != new.get(field):
            changes.append({
                "field": field,
                "old": old.get(field),
                "new": new.get(field)
            })
    
    return changes


async def _generate_changelog(version_id: str, db: AsyncSession) -> Changelog:
    """Generate a changelog from version changes."""
    # Get version and changes
    version_result = await db.execute(
        select(APIVersion).where(APIVersion.id == version_id)
    )
    version = version_result.scalar_one_or_none()
    
    changes_result = await db.execute(
        select(EndpointChange).where(EndpointChange.version_id == version_id)
    )
    changes = changes_result.scalars().all()
    
    # Categorize changes
    breaking = []
    new_endpoints = []
    modified = []
    deprecated = []
    removed = []
    
    for change in changes:
        item = {"path": change.path, "method": change.method, "description": change.description}
        
        if change.is_breaking:
            breaking.append(item)
        
        if change.change_type == "added":
            new_endpoints.append(item)
        elif change.change_type == "modified":
            modified.append(item)
        elif change.change_type == "deprecated":
            deprecated.append(item)
        elif change.change_type == "removed":
            removed.append(item)
    
    # Generate markdown
    markdown = f"# Changelog - {version.version}\n\n"
    
    if breaking:
        markdown += "## ⚠️ Breaking Changes\n"
        for b in breaking:
            markdown += f"- **{b['method']}** `{b['path']}` - {b['description']}\n"
        markdown += "\n"
    
    if new_endpoints:
        markdown += "## ✨ New Endpoints\n"
        for e in new_endpoints:
            markdown += f"- **{e['method']}** `{e['path']}`\n"
        markdown += "\n"
    
    if modified:
        markdown += "## 📝 Modified Endpoints\n"
        for m in modified:
            markdown += f"- **{m['method']}** `{m['path']}` - {m['description']}\n"
        markdown += "\n"
    
    if removed:
        markdown += "## 🗑️ Removed Endpoints\n"
        for r in removed:
            markdown += f"- **{r['method']}** `{r['path']}`\n"
    
    # Create changelog
    changelog = Changelog(
        version_id=version_id,
        content_markdown=markdown,
        breaking_changes=breaking,
        new_endpoints=new_endpoints,
        modified_endpoints=modified,
        deprecated_endpoints=deprecated,
        removed_endpoints=removed
    )
    
    db.add(changelog)
    await db.commit()
    await db.refresh(changelog)
    
    return changelog
