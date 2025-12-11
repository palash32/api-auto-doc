"""API endpoints for viewing and managing auto-generated documentation."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_async_db
from app.models.api_endpoint import APIEndpoint
from app.models.repository import Repository
from app.schemas.api_endpoint import (
    APIEndpointResponse, 
    PaginatedEndpoints, 
    APIEndpointUpdate
)
from app.api.auth import get_current_user_dependency
from app.api.dev_auth import get_current_user_optional

router = APIRouter()


@router.get("/repositories/{repo_id}/endpoints", response_model=PaginatedEndpoints)
async def list_repository_endpoints(
    repo_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in path or summary"),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List all API endpoints for a repository.
    
    Supports pagination, filtering by method/tag, and search.
    """
    # Verify repo exists and belongs to user's org
    repo_result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.organization_id == UUID(current_user["sub"])
        )
    )
    repo = repo_result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Build query
    query = select(APIEndpoint).where(APIEndpoint.repository_id == repo_id)
    
    # Apply filters
    if method:
        query = query.where(APIEndpoint.method == method.upper())
    
    if tag:
        query = query.where(APIEndpoint.tags.contains([tag]))
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (APIEndpoint.path.ilike(search_pattern)) | 
            (APIEndpoint.summary.ilike(search_pattern))
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(APIEndpoint.path)
    
    # Execute query
    result = await db.execute(query)
    endpoints = result.scalars().all()
    
    return PaginatedEndpoints(
        total=total,
        page=page,
        per_page=per_page,
        endpoints=endpoints
    )


@router.get("/endpoints/{endpoint_id}", response_model=APIEndpointResponse)
async def get_endpoint_detail(
    endpoint_id: UUID,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed information about a specific API endpoint.
    """
    # Get endpoint with repo check
    result = await db.execute(
        select(APIEndpoint)
        .join(Repository)
        .where(
            APIEndpoint.id == endpoint_id,
            Repository.organization_id == UUID(current_user["sub"])
        )
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    return endpoint


@router.patch("/endpoints/{endpoint_id}", response_model=APIEndpointResponse)
async def update_endpoint_documentation(
    endpoint_id: UUID,
    update_data: APIEndpointUpdate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update endpoint documentation manually.
    
    Allows users to refine AI-generated documentation.
    """
    # Get endpoint with repo check
    result = await db.execute(
        select(APIEndpoint)
        .join(Repository)
        .where(
            APIEndpoint.id == endpoint_id,
            Repository.organization_id == UUID(current_user["sub"])
        )
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    # Update fields
    if update_data.summary is not None:
        endpoint.summary = update_data.summary
    
    if update_data.description is not None:
        endpoint.description = update_data.description
    
    if update_data.tags is not None:
        endpoint.tags = update_data.tags

    if update_data.status is not None:
        endpoint.status = update_data.status
    
    await db.commit()
    await db.refresh(endpoint)
    
    return endpoint
