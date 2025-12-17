"""Performance and scalability API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.performance import (
    CDNConfig, CacheEntry, RateLimitConfig, RateLimitLog,
    BuildQueue, PerformanceMetric
)

router = APIRouter()


# ==================== Pydantic Schemas ====================

class CDNConfigResponse(BaseModel):
    id: str
    provider: str
    cdn_enabled: bool
    cdn_domain: Optional[str]
    cache_ttl_seconds: int
    auto_purge_on_update: bool


class CDNConfigUpdate(BaseModel):
    cdn_enabled: Optional[bool] = None
    cdn_domain: Optional[str] = None
    cache_ttl_seconds: Optional[int] = None
    auto_purge_on_update: Optional[bool] = None


class RateLimitResponse(BaseModel):
    tier: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    ai_requests_per_day: int


class RateLimitStatus(BaseModel):
    tier: str
    minute_used: int
    minute_limit: int
    hour_used: int
    hour_limit: int
    day_used: int
    day_limit: int


class QueueJobCreate(BaseModel):
    repository_id: str
    job_type: str
    payload: Optional[dict] = None
    priority: int = 5


class QueueJobResponse(BaseModel):
    id: str
    job_type: str
    priority: int
    status: str
    created_at: datetime


class PerformanceStats(BaseModel):
    avg_api_latency_ms: float
    cache_hit_rate: float
    queue_depth: int
    active_workers: int


# ==================== CDN Endpoints ====================

@router.get("/performance/cdn", response_model=Optional[CDNConfigResponse])
async def get_cdn_config(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get CDN configuration."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(CDNConfig).where(CDNConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        return None
    
    return CDNConfigResponse(
        id=str(config.id),
        provider=config.provider,
        cdn_enabled=config.cdn_enabled,
        cdn_domain=config.cdn_domain,
        cache_ttl_seconds=config.cache_ttl_seconds,
        auto_purge_on_update=config.auto_purge_on_update
    )


@router.post("/performance/cdn", response_model=CDNConfigResponse)
async def update_cdn_config(
    data: CDNConfigUpdate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Update CDN configuration."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(CDNConfig).where(CDNConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        config = CDNConfig(organization_id=org_id)
        db.add(config)
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    
    await db.commit()
    await db.refresh(config)
    
    return CDNConfigResponse(
        id=str(config.id),
        provider=config.provider,
        cdn_enabled=config.cdn_enabled,
        cdn_domain=config.cdn_domain,
        cache_ttl_seconds=config.cache_ttl_seconds,
        auto_purge_on_update=config.auto_purge_on_update
    )


@router.post("/performance/cdn/purge")
async def purge_cdn_cache(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Purge CDN cache."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(CDNConfig).where(CDNConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.last_purge_at = datetime.utcnow()
        await db.commit()
    
    # In production, would call CDN provider API
    return {"message": "Cache purge initiated", "purged_at": datetime.utcnow().isoformat()}


# ==================== Cache Endpoints ====================

@router.get("/performance/cache/stats")
async def get_cache_stats(
    db: AsyncSession = Depends(get_async_db)
):
    """Get cache statistics."""
    # Count entries by type
    result = await db.execute(
        select(
            CacheEntry.cache_type,
            func.count(CacheEntry.id).label("count"),
            func.sum(CacheEntry.size_bytes).label("total_size"),
            func.sum(CacheEntry.hit_count).label("total_hits")
        ).group_by(CacheEntry.cache_type)
    )
    stats = result.all()
    
    return {
        "entries_by_type": [
            {
                "type": s.cache_type,
                "count": s.count,
                "total_size_mb": round((s.total_size or 0) / 1024 / 1024, 2),
                "total_hits": s.total_hits or 0
            }
            for s in stats
        ],
        "total_entries": sum(s.count for s in stats) if stats else 0,
        "total_size_mb": round(sum((s.total_size or 0) for s in stats) / 1024 / 1024, 2) if stats else 0
    }


@router.post("/performance/cache/clear")
async def clear_cache(
    cache_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Clear cache entries."""
    query = select(CacheEntry)
    
    if cache_type:
        query = query.where(CacheEntry.cache_type == cache_type)
    
    result = await db.execute(query)
    entries = result.scalars().all()
    
    count = len(entries)
    for entry in entries:
        await db.delete(entry)
    
    await db.commit()
    
    return {"message": f"Cleared {count} cache entries"}


# ==================== Rate Limiting Endpoints ====================

@router.get("/performance/rate-limits", response_model=List[RateLimitResponse])
async def list_rate_limits(
    db: AsyncSession = Depends(get_async_db)
):
    """List rate limit configurations by tier."""
    result = await db.execute(
        select(RateLimitConfig).order_by(RateLimitConfig.requests_per_day)
    )
    configs = result.scalars().all()
    
    return [
        RateLimitResponse(
            tier=c.tier,
            requests_per_minute=c.requests_per_minute,
            requests_per_hour=c.requests_per_hour,
            requests_per_day=c.requests_per_day,
            ai_requests_per_day=c.ai_requests_per_day
        )
        for c in configs
    ]


@router.post("/performance/rate-limits/seed")
async def seed_rate_limits(
    db: AsyncSession = Depends(get_async_db)
):
    """Seed default rate limit configurations."""
    configs = [
        RateLimitConfig(
            tier="free",
            requests_per_minute=30,
            requests_per_hour=500,
            requests_per_day=5000,
            ai_requests_per_day=50,
            export_requests_per_day=5,
            scan_requests_per_hour=2
        ),
        RateLimitConfig(
            tier="starter",
            requests_per_minute=60,
            requests_per_hour=2000,
            requests_per_day=20000,
            ai_requests_per_day=200,
            export_requests_per_day=20,
            scan_requests_per_hour=10
        ),
        RateLimitConfig(
            tier="pro",
            requests_per_minute=120,
            requests_per_hour=5000,
            requests_per_day=50000,
            ai_requests_per_day=500,
            export_requests_per_day=50,
            scan_requests_per_hour=30
        ),
        RateLimitConfig(
            tier="enterprise",
            requests_per_minute=300,
            requests_per_hour=20000,
            requests_per_day=200000,
            ai_requests_per_day=2000,
            export_requests_per_day=200,
            scan_requests_per_hour=100
        )
    ]
    
    for config in configs:
        db.add(config)
    
    await db.commit()
    
    return {"message": f"Seeded {len(configs)} rate limit configurations"}


@router.get("/performance/rate-limits/status", response_model=RateLimitStatus)
async def get_rate_limit_status(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get current rate limit status for organization."""
    org_id = current_user.get("organization_id")
    tier = current_user.get("tier", "free")
    
    now = datetime.utcnow()
    
    # Get tier limits
    config_result = await db.execute(
        select(RateLimitConfig).where(RateLimitConfig.tier == tier)
    )
    config = config_result.scalar_one_or_none()
    
    if not config:
        # Default limits
        config = RateLimitConfig(
            tier="free",
            requests_per_minute=30,
            requests_per_hour=500,
            requests_per_day=5000
        )
    
    # Get current usage
    minute_start = now.replace(second=0, microsecond=0)
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    async def get_count(window_start: datetime) -> int:
        result = await db.execute(
            select(func.coalesce(func.sum(RateLimitLog.request_count), 0))
            .where(
                RateLimitLog.organization_id == org_id,
                RateLimitLog.window_start >= window_start
            )
        )
        return result.scalar() or 0
    
    return RateLimitStatus(
        tier=tier,
        minute_used=await get_count(minute_start),
        minute_limit=config.requests_per_minute,
        hour_used=await get_count(hour_start),
        hour_limit=config.requests_per_hour,
        day_used=await get_count(day_start),
        day_limit=config.requests_per_day
    )


# ==================== Build Queue Endpoints ====================

@router.get("/performance/queue", response_model=List[QueueJobResponse])
async def list_queue(
    status: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List build queue jobs."""
    query = select(BuildQueue)
    
    if status:
        query = query.where(BuildQueue.status == status)
    
    query = query.order_by(
        desc(BuildQueue.priority + BuildQueue.tier_boost),
        BuildQueue.created_at
    ).limit(limit)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return [
        QueueJobResponse(
            id=str(j.id),
            job_type=j.job_type,
            priority=j.priority + j.tier_boost,
            status=j.status,
            created_at=j.created_at
        )
        for j in jobs
    ]


@router.post("/performance/queue", response_model=QueueJobResponse)
async def enqueue_job(
    data: QueueJobCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Add job to build queue."""
    org_id = current_user.get("organization_id")
    tier = current_user.get("tier", "free")
    
    # Calculate tier boost
    tier_boosts = {"free": 0, "starter": 1, "pro": 2, "enterprise": 5}
    
    job = BuildQueue(
        organization_id=org_id,
        repository_id=data.repository_id,
        job_type=data.job_type,
        payload=data.payload,
        priority=data.priority,
        tier_boost=tier_boosts.get(tier, 0)
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return QueueJobResponse(
        id=str(job.id),
        job_type=job.job_type,
        priority=job.priority + job.tier_boost,
        status=job.status,
        created_at=job.created_at
    )


@router.get("/performance/queue/stats")
async def get_queue_stats(
    db: AsyncSession = Depends(get_async_db)
):
    """Get queue statistics."""
    result = await db.execute(
        select(
            BuildQueue.status,
            func.count(BuildQueue.id).label("count")
        ).group_by(BuildQueue.status)
    )
    stats = {s.status: s.count for s in result.all()}
    
    # Also get stuck jobs count (processing for > 30 min)
    stuck_cutoff = datetime.utcnow() - timedelta(minutes=30)
    stuck_result = await db.execute(
        select(func.count(BuildQueue.id))
        .where(
            BuildQueue.status == "processing",
            BuildQueue.started_at < stuck_cutoff
        )
    )
    stuck_count = stuck_result.scalar() or 0
    
    return {
        "pending": stats.get("pending", 0),
        "processing": stats.get("processing", 0),
        "completed": stats.get("completed", 0),
        "failed": stats.get("failed", 0),
        "stuck": stuck_count,
        "total": sum(stats.values())
    }


@router.post("/performance/queue/recover-stuck")
async def recover_stuck_jobs(
    max_age_minutes: int = Query(default=30, ge=5, le=120),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Recover jobs that are stuck in 'processing' state.
    
    Jobs stuck for longer than max_age_minutes are reset to 'pending'
    with an incremented retry count.
    """
    stuck_cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    
    # Find stuck jobs
    result = await db.execute(
        select(BuildQueue)
        .where(
            BuildQueue.status == "processing",
            BuildQueue.started_at < stuck_cutoff
        )
    )
    stuck_jobs = result.scalars().all()
    
    recovered = 0
    failed = 0
    
    for job in stuck_jobs:
        if job.retry_count >= job.max_retries:
            # Max retries exceeded, mark as failed
            job.status = "failed"
            job.error_message = f"Max retries ({job.max_retries}) exceeded after stuck recovery"
            job.completed_at = datetime.utcnow()
            failed += 1
        else:
            # Reset to pending for retry
            job.status = "pending"
            job.retry_count += 1
            job.worker_id = None
            job.started_at = None
            job.error_message = f"Recovered from stuck state (attempt {job.retry_count})"
            recovered += 1
    
    await db.commit()
    
    return {
        "message": f"Processed {len(stuck_jobs)} stuck jobs",
        "recovered": recovered,
        "failed_max_retries": failed,
        "cutoff_minutes": max_age_minutes
    }


@router.post("/performance/queue/{job_id}/retry")
async def retry_failed_job(
    job_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Retry a failed job by resetting it to pending."""
    result = await db.execute(
        select(BuildQueue).where(BuildQueue.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in ["failed", "processing"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot retry job with status '{job.status}'"
        )
    
    # Reset job for retry
    job.status = "pending"
    job.retry_count += 1
    job.worker_id = None
    job.started_at = None
    job.completed_at = None
    job.error_message = None
    
    await db.commit()
    
    return {
        "message": "Job reset for retry",
        "job_id": str(job.id),
        "retry_count": job.retry_count
    }


@router.delete("/performance/queue/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Cancel a pending or failed job."""
    result = await db.execute(
        select(BuildQueue).where(BuildQueue.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == "processing":
        raise HTTPException(
            status_code=400, 
            detail="Cannot cancel a job that is currently processing"
        )
    
    await db.delete(job)
    await db.commit()
    
    return {"message": "Job cancelled", "job_id": job_id}


# ==================== Performance Metrics ====================

@router.get("/performance/metrics")
async def get_performance_metrics(
    minutes: int = Query(default=60, ge=1, le=1440),
    db: AsyncSession = Depends(get_async_db)
):
    """Get recent performance metrics."""
    since = datetime.utcnow() - timedelta(minutes=minutes)
    
    result = await db.execute(
        select(
            PerformanceMetric.metric_name,
            func.avg(PerformanceMetric.metric_value).label("avg_value"),
            func.min(PerformanceMetric.metric_value).label("min_value"),
            func.max(PerformanceMetric.metric_value).label("max_value")
        )
        .where(PerformanceMetric.recorded_at >= since)
        .group_by(PerformanceMetric.metric_name)
    )
    metrics = result.all()
    
    return {
        m.metric_name: {
            "avg": round(m.avg_value, 2),
            "min": round(m.min_value, 2),
            "max": round(m.max_value, 2)
        }
        for m in metrics
    }


@router.get("/performance/dashboard", response_model=PerformanceStats)
async def get_performance_dashboard(
    db: AsyncSession = Depends(get_async_db)
):
    """Get performance dashboard summary."""
    # Get average API latency
    latency_result = await db.execute(
        select(func.avg(PerformanceMetric.metric_value))
        .where(
            PerformanceMetric.metric_name == "api_latency",
            PerformanceMetric.recorded_at >= datetime.utcnow() - timedelta(hours=1)
        )
    )
    avg_latency = latency_result.scalar() or 50.0
    
    # Get cache hit rate
    cache_result = await db.execute(
        select(func.avg(PerformanceMetric.metric_value))
        .where(
            PerformanceMetric.metric_name == "cache_hit_rate",
            PerformanceMetric.recorded_at >= datetime.utcnow() - timedelta(hours=1)
        )
    )
    cache_rate = cache_result.scalar() or 85.0
    
    # Get queue depth
    queue_result = await db.execute(
        select(func.count(BuildQueue.id))
        .where(BuildQueue.status == "pending")
    )
    queue_depth = queue_result.scalar() or 0
    
    # Active workers (simulated)
    active_workers = 4
    
    return PerformanceStats(
        avg_api_latency_ms=round(avg_latency, 2),
        cache_hit_rate=round(cache_rate, 2),
        queue_depth=queue_depth,
        active_workers=active_workers
    )
