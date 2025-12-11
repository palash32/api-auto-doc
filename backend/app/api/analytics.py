"""Analytics API endpoints for dashboard and reporting."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from uuid import uuid4
import uuid

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.analytics import (
    EndpointView, EndpointUsageStats, DocumentationHealth,
    APILatencyMetric, AnalyticsSummary
)
from app.models.api_endpoint import APIEndpoint
from app.models.repository import Repository

router = APIRouter()


# ==================== Pydantic Schemas ====================

class EndpointViewCreate(BaseModel):
    endpoint_id: str
    session_id: Optional[str] = None
    referrer: Optional[str] = None


class TopEndpointResponse(BaseModel):
    endpoint_id: str
    path: str
    method: str
    view_count: int
    repository_name: Optional[str] = None


class HealthScoreResponse(BaseModel):
    repository_id: str
    repository_name: str
    health_score: int
    description_coverage: int
    parameter_coverage: int
    example_coverage: int
    total_endpoints: int
    undocumented_endpoints: int


class DashboardSummary(BaseModel):
    total_views: int
    unique_visitors: int
    total_endpoints: int
    avg_health_score: float
    playground_requests: int
    avg_latency_ms: Optional[float]
    views_trend: float  # % change from previous period
    top_endpoints: List[TopEndpointResponse]


class LatencyTrendPoint(BaseModel):
    date: str
    avg_latency: float
    p95_latency: float
    error_rate: float


# ==================== View Tracking Endpoints ====================

@router.post("/track/view")
async def track_endpoint_view(
    data: EndpointViewCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Track an endpoint page view."""
    view = EndpointView(
        endpoint_id=data.endpoint_id,
        user_id=current_user.get("id") if current_user else None,
        session_id=data.session_id,
        referrer=data.referrer
    )
    
    db.add(view)
    await db.commit()
    
    return {"message": "View tracked"}


@router.post("/track/playground")
async def track_playground_usage(
    endpoint_id: Optional[str] = None,
    latency_ms: Optional[float] = None,
    status_code: Optional[int] = None,
    url: str = "",
    method: str = "GET",
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Track playground API request for latency monitoring."""
    metric = APILatencyMetric(
        endpoint_id=endpoint_id,
        url=url,
        method=method,
        latency_ms=latency_ms or 0,
        status_code=status_code,
        tested_by_id=current_user.get("id") if current_user else None,
        is_error=status_code is not None and status_code >= 400
    )
    
    db.add(metric)
    await db.commit()
    
    return {"message": "Playground usage tracked"}


# ==================== Dashboard Endpoints ====================

@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    days: int = Query(default=7, ge=1, le=90),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get analytics dashboard summary."""
    org_id = current_user.get("organization_id")
    start_date = datetime.utcnow() - timedelta(days=days)
    prev_start = start_date - timedelta(days=days)
    
    # Total views in period
    views_result = await db.execute(
        select(func.count(EndpointView.id))
        .join(APIEndpoint, EndpointView.endpoint_id == APIEndpoint.id)
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(
            Repository.organization_id == org_id,
            EndpointView.viewed_at >= start_date
        )
    )
    total_views = views_result.scalar() or 0
    
    # Previous period views for trend
    prev_views_result = await db.execute(
        select(func.count(EndpointView.id))
        .join(APIEndpoint, EndpointView.endpoint_id == APIEndpoint.id)
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(
            Repository.organization_id == org_id,
            EndpointView.viewed_at >= prev_start,
            EndpointView.viewed_at < start_date
        )
    )
    prev_views = prev_views_result.scalar() or 1  # Avoid division by zero
    views_trend = ((total_views - prev_views) / prev_views) * 100 if prev_views > 0 else 0
    
    # Unique visitors (by session_id)
    unique_result = await db.execute(
        select(func.count(func.distinct(EndpointView.session_id)))
        .join(APIEndpoint, EndpointView.endpoint_id == APIEndpoint.id)
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(
            Repository.organization_id == org_id,
            EndpointView.viewed_at >= start_date
        )
    )
    unique_visitors = unique_result.scalar() or 0
    
    # Total endpoints
    endpoints_result = await db.execute(
        select(func.count(APIEndpoint.id))
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(Repository.organization_id == org_id)
    )
    total_endpoints = endpoints_result.scalar() or 0
    
    # Average health score
    health_result = await db.execute(
        select(func.avg(DocumentationHealth.health_score))
        .join(Repository, DocumentationHealth.repository_id == Repository.id)
        .where(Repository.organization_id == org_id)
    )
    avg_health = health_result.scalar() or 0
    
    # Playground requests
    playground_result = await db.execute(
        select(func.count(APILatencyMetric.id))
        .where(APILatencyMetric.tested_at >= start_date)
    )
    playground_requests = playground_result.scalar() or 0
    
    # Average latency
    latency_result = await db.execute(
        select(func.avg(APILatencyMetric.latency_ms))
        .where(
            APILatencyMetric.tested_at >= start_date,
            APILatencyMetric.is_error == False
        )
    )
    avg_latency = latency_result.scalar()
    
    # Top endpoints
    top_result = await db.execute(
        select(
            EndpointView.endpoint_id,
            APIEndpoint.path,
            APIEndpoint.method,
            func.count(EndpointView.id).label('view_count'),
            Repository.name.label('repo_name')
        )
        .join(APIEndpoint, EndpointView.endpoint_id == APIEndpoint.id)
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(
            Repository.organization_id == org_id,
            EndpointView.viewed_at >= start_date
        )
        .group_by(EndpointView.endpoint_id, APIEndpoint.path, APIEndpoint.method, Repository.name)
        .order_by(desc('view_count'))
        .limit(10)
    )
    top_rows = top_result.all()
    
    top_endpoints = [
        TopEndpointResponse(
            endpoint_id=str(row.endpoint_id),
            path=row.path,
            method=row.method,
            view_count=row.view_count,
            repository_name=row.repo_name
        )
        for row in top_rows
    ]
    
    return DashboardSummary(
        total_views=total_views,
        unique_visitors=unique_visitors,
        total_endpoints=total_endpoints,
        avg_health_score=round(avg_health, 1),
        playground_requests=playground_requests,
        avg_latency_ms=round(avg_latency, 2) if avg_latency else None,
        views_trend=round(views_trend, 1),
        top_endpoints=top_endpoints
    )


# ==================== Health Score Endpoints ====================

@router.get("/health", response_model=List[HealthScoreResponse])
async def get_health_scores(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get documentation health scores for all repositories."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(DocumentationHealth, Repository)
        .join(Repository, DocumentationHealth.repository_id == Repository.id)
        .where(Repository.organization_id == org_id)
        .order_by(desc(DocumentationHealth.calculated_at))
    )
    rows = result.all()
    
    # Get latest health score per repo
    seen_repos = set()
    health_scores = []
    
    for health, repo in rows:
        if repo.id not in seen_repos:
            seen_repos.add(repo.id)
            health_scores.append(HealthScoreResponse(
                repository_id=str(health.repository_id),
                repository_name=repo.name,
                health_score=health.health_score,
                description_coverage=health.description_coverage,
                parameter_coverage=health.parameter_coverage,
                example_coverage=health.example_coverage,
                total_endpoints=health.total_endpoints,
                undocumented_endpoints=health.undocumented_endpoints
            ))
    
    return health_scores


@router.post("/health/calculate/{repository_id}")
async def calculate_health_score(
    repository_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Calculate and store documentation health score for a repository."""
    # Get repository
    repo_result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repo = repo_result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Get endpoints
    endpoints_result = await db.execute(
        select(APIEndpoint).where(APIEndpoint.repository_id == repository_id)
    )
    endpoints = endpoints_result.scalars().all()
    
    total = len(endpoints)
    if total == 0:
        return {"health_score": 0, "message": "No endpoints found"}
    
    # Calculate coverage
    with_desc = sum(1 for e in endpoints if e.description and len(e.description) > 10)
    with_params = sum(1 for e in endpoints if e.parameters)
    with_examples = sum(1 for e in endpoints if e.request_example or e.response_example)
    
    desc_coverage = int((with_desc / total) * 100)
    param_coverage = int((with_params / total) * 100)
    example_coverage = int((with_examples / total) * 100)
    
    # Overall score (weighted average)
    health_score = int(
        desc_coverage * 0.4 +
        param_coverage * 0.3 +
        example_coverage * 0.3
    )
    
    # Store result
    health = DocumentationHealth(
        repository_id=repository_id,
        health_score=health_score,
        description_coverage=desc_coverage,
        parameter_coverage=param_coverage,
        example_coverage=example_coverage,
        total_endpoints=total,
        documented_endpoints=with_desc,
        undocumented_endpoints=total - with_desc
    )
    
    db.add(health)
    await db.commit()
    
    return {
        "health_score": health_score,
        "description_coverage": desc_coverage,
        "parameter_coverage": param_coverage,
        "example_coverage": example_coverage,
        "total_endpoints": total
    }


# ==================== Latency Endpoints ====================

@router.get("/latency/trend", response_model=List[LatencyTrendPoint])
async def get_latency_trend(
    days: int = Query(default=7, ge=1, le=30),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get API latency trend over time."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.date(APILatencyMetric.tested_at).label('date'),
            func.avg(APILatencyMetric.latency_ms).label('avg_latency'),
            func.percentile_cont(0.95).within_group(
                APILatencyMetric.latency_ms
            ).label('p95_latency'),
            (func.sum(func.cast(APILatencyMetric.is_error, Integer)) * 100.0 / 
             func.count(APILatencyMetric.id)).label('error_rate')
        )
        .where(APILatencyMetric.tested_at >= start_date)
        .group_by(func.date(APILatencyMetric.tested_at))
        .order_by('date')
    )
    rows = result.all()
    
    return [
        LatencyTrendPoint(
            date=str(row.date),
            avg_latency=round(row.avg_latency or 0, 2),
            p95_latency=round(row.p95_latency or 0, 2),
            error_rate=round(row.error_rate or 0, 2)
        )
        for row in rows
    ]


# ==================== Top Endpoints ====================

@router.get("/top-endpoints", response_model=List[TopEndpointResponse])
async def get_top_endpoints(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get most viewed endpoints."""
    org_id_str = current_user.get("organization_id") if current_user else None
    
    # Return empty list if no org context or invalid UUID
    if not org_id_str:
        return []
    
    try:
        org_id = uuid.UUID(org_id_str)
    except (ValueError, TypeError):
        return []
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            EndpointView.endpoint_id,
            APIEndpoint.path,
            APIEndpoint.method,
            func.count(EndpointView.id).label('view_count'),
            Repository.name.label('repo_name')
        )
        .join(APIEndpoint, EndpointView.endpoint_id == APIEndpoint.id)
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(
            Repository.organization_id == org_id,
            EndpointView.viewed_at >= start_date
        )
        .group_by(EndpointView.endpoint_id, APIEndpoint.path, APIEndpoint.method, Repository.name)
        .order_by(desc('view_count'))
        .limit(limit)
    )
    rows = result.all()
    
    return [
        TopEndpointResponse(
            endpoint_id=str(row.endpoint_id),
            path=row.path,
            method=row.method,
            view_count=row.view_count,
            repository_name=row.repo_name
        )
        for row in rows
    ]
