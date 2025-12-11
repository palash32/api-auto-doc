"""Performance and scalability models for CDN, caching, rate limiting, and queues."""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
import enum

from app.core.database import Base


class RateLimitTier(enum.Enum):
    """Rate limit tiers."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class QueuePriority(enum.Enum):
    """Queue priority levels."""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class CDNConfig(Base):
    """
    CDN configuration for static assets.
    """
    __tablename__ = "cdn_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # CDN settings
    provider = Column(String(50), default="cloudflare")  # cloudflare, aws_cloudfront, fastly
    cdn_enabled = Column(Boolean, default=False)
    
    # URLs
    cdn_domain = Column(String(200), nullable=True)
    origin_url = Column(String(500), nullable=True)
    
    # Cache settings
    cache_ttl_seconds = Column(Integer, default=86400)  # 24 hours
    cache_static_assets = Column(Boolean, default=True)
    cache_api_responses = Column(Boolean, default=False)
    
    # Purge settings
    auto_purge_on_update = Column(Boolean, default=True)
    last_purge_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CacheEntry(Base):
    """
    Cache entry tracking.
    """
    __tablename__ = "cache_entries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Cache key
    cache_key = Column(String(500), nullable=False, unique=True, index=True)
    cache_type = Column(String(50), nullable=False)  # api_response, static_asset, query_result
    
    # Metadata
    content_hash = Column(String(64), nullable=True)
    size_bytes = Column(Integer, default=0)
    
    # TTL
    expires_at = Column(DateTime, nullable=True)
    
    # Stats
    hit_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class RateLimitConfig(Base):
    """
    Rate limiting configuration per tier.
    """
    __tablename__ = "rate_limit_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Tier
    tier = Column(String(20), nullable=False, unique=True)  # free, starter, pro, enterprise
    
    # Limits
    requests_per_minute = Column(Integer, default=60)
    requests_per_hour = Column(Integer, default=1000)
    requests_per_day = Column(Integer, default=10000)
    
    # Burst limits
    burst_limit = Column(Integer, default=10)
    burst_window_seconds = Column(Integer, default=1)
    
    # Specific endpoint limits
    ai_requests_per_day = Column(Integer, default=100)
    export_requests_per_day = Column(Integer, default=10)
    scan_requests_per_hour = Column(Integer, default=5)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RateLimitLog(Base):
    """
    Rate limit tracking per organization.
    """
    __tablename__ = "rate_limit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Window
    window_type = Column(String(20), nullable=False)  # minute, hour, day
    window_start = Column(DateTime, nullable=False)
    
    # Counts
    request_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class BuildQueue(Base):
    """
    Build queue with priority management.
    """
    __tablename__ = "build_queue"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # Job details
    job_type = Column(String(50), nullable=False)  # scan, export, ai_enhance
    payload = Column(JSON, nullable=True)
    
    # Priority
    priority = Column(Integer, default=5)  # 1-10, higher = more urgent
    tier_boost = Column(Integer, default=0)  # Extra priority from subscription tier
    
    # Status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    
    # Processing
    worker_id = Column(String(50), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Retry
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Error
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="build_queue_jobs")
    repository = relationship("Repository", backref="build_queue_jobs")


class PerformanceMetric(Base):
    """
    Track system performance metrics.
    """
    __tablename__ = "performance_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Metric details
    metric_name = Column(String(100), nullable=False)  # api_latency, db_query_time, cache_hit_rate
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # ms, %, count
    
    # Context
    endpoint = Column(String(200), nullable=True)
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow)
