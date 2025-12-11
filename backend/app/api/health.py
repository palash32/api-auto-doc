"""Health monitoring API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import httpx
import asyncio
import uuid

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.health import (
    HealthCheck, EndpointHealthSummary, HealthAlert,
    AlertConfig, HealthCheckSchedule
)
from app.models.api_endpoint import APIEndpoint
from app.models.repository import Repository

router = APIRouter()


# ==================== Pydantic Schemas ====================

class HealthCheckResponse(BaseModel):
    id: str
    url: str
    method: str
    status: str
    status_code: Optional[int]
    latency_ms: Optional[float]
    is_error: bool
    error_message: Optional[str]
    checked_at: datetime


class HealthSummaryResponse(BaseModel):
    endpoint_id: str
    path: str
    method: str
    current_status: str
    last_checked_at: Optional[datetime]
    latency_p50: Optional[float]
    latency_p95: Optional[float]
    latency_p99: Optional[float]
    uptime_24h: float
    uptime_7d: float
    uptime_30d: float
    total_checks: int


class AlertResponse(BaseModel):
    id: str
    alert_type: str
    severity: str
    title: str
    message: Optional[str]
    is_resolved: bool
    created_at: datetime


class AlertConfigCreate(BaseModel):
    channel: str  # email, slack, pagerduty, webhook
    channel_config: Optional[dict] = None
    latency_threshold_ms: int = 1000
    error_rate_threshold: float = 5.0
    alert_on_down: bool = True
    alert_on_degraded: bool = True
    alert_on_high_latency: bool = True
    alert_on_recovery: bool = True


class RunHealthCheckRequest(BaseModel):
    url: str
    method: str = "GET"
    endpoint_id: Optional[str] = None
    timeout_seconds: int = 30


# ==================== Health Check Endpoints ====================

@router.post("/health/check", response_model=HealthCheckResponse)
async def run_health_check(
    request: RunHealthCheckRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Run an immediate health check on a URL."""
    org_id = current_user.get("organization_id")
    
    # Perform the health check
    result = await _perform_health_check(
        url=request.url,
        method=request.method,
        timeout=request.timeout_seconds
    )
    
    # Get repository from endpoint if provided
    repo_id = None
    if request.endpoint_id:
        ep_result = await db.execute(
            select(APIEndpoint).where(APIEndpoint.id == request.endpoint_id)
        )
        endpoint = ep_result.scalar_one_or_none()
        if endpoint:
            repo_id = endpoint.repository_id
    
    # Store the result
    health_check = HealthCheck(
        endpoint_id=request.endpoint_id,
        repository_id=repo_id or "unknown",
        url=request.url,
        method=request.method,
        status=result["status"],
        status_code=result.get("status_code"),
        latency_ms=result.get("latency_ms"),
        is_error=result.get("is_error", False),
        error_message=result.get("error_message"),
        response_size_bytes=result.get("response_size")
    )
    
    db.add(health_check)
    await db.commit()
    await db.refresh(health_check)
    
    # Update summary in background
    if request.endpoint_id:
        background_tasks.add_task(_update_health_summary, request.endpoint_id, db)
    
    return HealthCheckResponse(
        id=str(health_check.id),
        url=health_check.url,
        method=health_check.method,
        status=health_check.status,
        status_code=health_check.status_code,
        latency_ms=health_check.latency_ms,
        is_error=health_check.is_error,
        error_message=health_check.error_message,
        checked_at=health_check.checked_at
    )


@router.get("/health/endpoints/{endpoint_id}", response_model=HealthSummaryResponse)
async def get_endpoint_health(
    endpoint_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get health summary for a specific endpoint."""
    result = await db.execute(
        select(EndpointHealthSummary, APIEndpoint)
        .join(APIEndpoint, EndpointHealthSummary.endpoint_id == APIEndpoint.id)
        .where(EndpointHealthSummary.endpoint_id == endpoint_id)
    )
    row = result.first()
    
    if not row:
        # Return default summary if none exists
        ep_result = await db.execute(
            select(APIEndpoint).where(APIEndpoint.id == endpoint_id)
        )
        endpoint = ep_result.scalar_one_or_none()
        if not endpoint:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        return HealthSummaryResponse(
            endpoint_id=endpoint_id,
            path=endpoint.path,
            method=endpoint.method,
            current_status="unknown",
            last_checked_at=None,
            latency_p50=None,
            latency_p95=None,
            latency_p99=None,
            uptime_24h=100.0,
            uptime_7d=100.0,
            uptime_30d=100.0,
            total_checks=0
        )
    
    summary, endpoint = row
    
    return HealthSummaryResponse(
        endpoint_id=str(summary.endpoint_id),
        path=endpoint.path,
        method=endpoint.method,
        current_status=summary.current_status,
        last_checked_at=summary.last_checked_at,
        latency_p50=summary.latency_p50,
        latency_p95=summary.latency_p95,
        latency_p99=summary.latency_p99,
        uptime_24h=summary.uptime_24h,
        uptime_7d=summary.uptime_7d,
        uptime_30d=summary.uptime_30d,
        total_checks=summary.total_checks
    )


@router.get("/health/repositories/{repository_id}", response_model=List[HealthSummaryResponse])
async def get_repository_health(
    repository_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get health summary for all endpoints in a repository."""
    result = await db.execute(
        select(EndpointHealthSummary, APIEndpoint)
        .join(APIEndpoint, EndpointHealthSummary.endpoint_id == APIEndpoint.id)
        .where(APIEndpoint.repository_id == repository_id)
        .order_by(desc(EndpointHealthSummary.updated_at))
    )
    rows = result.all()
    
    return [
        HealthSummaryResponse(
            endpoint_id=str(summary.endpoint_id),
            path=endpoint.path,
            method=endpoint.method,
            current_status=summary.current_status,
            last_checked_at=summary.last_checked_at,
            latency_p50=summary.latency_p50,
            latency_p95=summary.latency_p95,
            latency_p99=summary.latency_p99,
            uptime_24h=summary.uptime_24h,
            uptime_7d=summary.uptime_7d,
            uptime_30d=summary.uptime_30d,
            total_checks=summary.total_checks
        )
        for summary, endpoint in rows
    ]


@router.get("/health/history/{endpoint_id}", response_model=List[HealthCheckResponse])
async def get_health_history(
    endpoint_id: str,
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get health check history for an endpoint."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(HealthCheck)
        .where(
            HealthCheck.endpoint_id == endpoint_id,
            HealthCheck.checked_at >= start_date
        )
        .order_by(desc(HealthCheck.checked_at))
        .limit(limit)
    )
    checks = result.scalars().all()
    
    return [
        HealthCheckResponse(
            id=str(c.id),
            url=c.url,
            method=c.method,
            status=c.status,
            status_code=c.status_code,
            latency_ms=c.latency_ms,
            is_error=c.is_error,
            error_message=c.error_message,
            checked_at=c.checked_at
        )
        for c in checks
    ]


# ==================== Alert Endpoints ====================

@router.get("/health/alerts", response_model=List[AlertResponse])
async def list_alerts(
    resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List health alerts for the organization."""
    org_id = current_user.get("organization_id")
    
    query = select(HealthAlert).where(HealthAlert.organization_id == org_id)
    
    if resolved is not None:
        query = query.where(HealthAlert.is_resolved == resolved)
    
    if severity:
        query = query.where(HealthAlert.severity == severity)
    
    query = query.order_by(desc(HealthAlert.created_at)).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [
        AlertResponse(
            id=str(a.id),
            alert_type=a.alert_type,
            severity=a.severity,
            title=a.title,
            message=a.message,
            is_resolved=a.is_resolved,
            created_at=a.created_at
        )
        for a in alerts
    ]


@router.post("/health/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Mark an alert as resolved."""
    result = await db.execute(
        select(HealthAlert).where(HealthAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.acknowledged_by_id = current_user.get("id")
    alert.acknowledged_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Alert resolved"}


# ==================== Alert Configuration ====================

@router.get("/health/alerts/config", response_model=List[dict])
async def list_alert_configs(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List alert configurations."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.organization_id == org_id)
    )
    configs = result.scalars().all()
    
    return [
        {
            "id": str(c.id),
            "channel": c.channel,
            "channel_config": c.channel_config,
            "latency_threshold_ms": c.latency_threshold_ms,
            "error_rate_threshold": c.error_rate_threshold,
            "alert_on_down": c.alert_on_down,
            "alert_on_degraded": c.alert_on_degraded,
            "is_enabled": c.is_enabled
        }
        for c in configs
    ]


@router.post("/health/alerts/config")
async def create_alert_config(
    data: AlertConfigCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create alert configuration."""
    org_id = current_user.get("organization_id")
    
    config = AlertConfig(
        organization_id=org_id,
        channel=data.channel,
        channel_config=data.channel_config,
        latency_threshold_ms=data.latency_threshold_ms,
        error_rate_threshold=data.error_rate_threshold,
        alert_on_down=data.alert_on_down,
        alert_on_degraded=data.alert_on_degraded,
        alert_on_high_latency=data.alert_on_high_latency,
        alert_on_recovery=data.alert_on_recovery
    )
    
    db.add(config)
    await db.commit()
    
    return {"message": "Alert config created", "id": str(config.id)}


# ==================== Dashboard Stats ====================

@router.get("/health/dashboard")
async def get_health_dashboard(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get health monitoring dashboard summary."""
    org_id_str = current_user.get("organization_id") if current_user else None
    
    # Return safe defaults if no organization context
    if not org_id_str:
        return {
            "total_endpoints": 0,
            "status_breakdown": {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
                "unknown": 0
            },
            "avg_uptime_24h": 100.0,
            "avg_latency_ms": None,
            "open_alerts": 0
        }
    
    # Convert org_id string to UUID
    try:
        org_id = uuid.UUID(org_id_str)
    except (ValueError, TypeError):
        return {
            "total_endpoints": 0,
            "status_breakdown": {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
                "unknown": 0
            },
            "avg_uptime_24h": 100.0,
            "avg_latency_ms": None,
            "open_alerts": 0
        }
    
    # Get all endpoints for org
    endpoints_result = await db.execute(
        select(func.count(APIEndpoint.id))
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(Repository.organization_id == org_id)
    )
    total_endpoints = endpoints_result.scalar() or 0
    
    # Get health summaries
    summary_result = await db.execute(
        select(EndpointHealthSummary)
        .join(APIEndpoint, EndpointHealthSummary.endpoint_id == APIEndpoint.id)
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(Repository.organization_id == org_id)
    )
    summaries = summary_result.scalars().all()
    
    # Calculate stats
    healthy = sum(1 for s in summaries if s.current_status == "healthy")
    degraded = sum(1 for s in summaries if s.current_status == "degraded")
    unhealthy = sum(1 for s in summaries if s.current_status == "unhealthy")
    unknown = total_endpoints - len(summaries)
    
    # Average uptime
    avg_uptime = sum(s.uptime_24h for s in summaries) / len(summaries) if summaries else 100.0
    
    # Average latency
    latencies = [s.latency_p50 for s in summaries if s.latency_p50]
    avg_latency = sum(latencies) / len(latencies) if latencies else None
    
    # Recent alerts
    alerts_result = await db.execute(
        select(func.count(HealthAlert.id))
        .where(
            HealthAlert.organization_id == org_id,
            HealthAlert.is_resolved == False
        )
    )
    open_alerts = alerts_result.scalar() or 0
    
    return {
        "total_endpoints": total_endpoints,
        "status_breakdown": {
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "unknown": unknown
        },
        "avg_uptime_24h": round(avg_uptime, 2),
        "avg_latency_ms": round(avg_latency, 2) if avg_latency else None,
        "open_alerts": open_alerts
    }


# ==================== Helper Functions ====================

async def _perform_health_check(url: str, method: str = "GET", timeout: int = 30) -> dict:
    """Perform an actual HTTP health check."""
    try:
        start_time = datetime.utcnow()
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method.upper(), url)
        
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000
        
        # Determine status
        if response.status_code < 300:
            status = "healthy"
        elif response.status_code < 500:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "status_code": response.status_code,
            "latency_ms": round(latency_ms, 2),
            "is_error": False,
            "response_size": len(response.content)
        }
    
    except httpx.TimeoutException:
        return {
            "status": "unhealthy",
            "is_error": True,
            "error_message": f"Request timed out after {timeout}s"
        }
    except httpx.ConnectError as e:
        return {
            "status": "unhealthy",
            "is_error": True,
            "error_message": f"Connection failed: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "is_error": True,
            "error_message": str(e)
        }


async def _update_health_summary(endpoint_id: str, db: AsyncSession):
    """Update the health summary for an endpoint based on recent checks."""
    # This would typically be run as a background task
    # Implementation would aggregate recent health checks and update summary
    pass
