"""Health monitoring models for endpoint status and alerts."""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
import enum

from app.core.database import Base


class HealthStatus(enum.Enum):
    """Possible health statuses."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertSeverity(enum.Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(enum.Enum):
    """Alert notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"


class HealthCheck(Base):
    """
    Individual health check result for an endpoint.
    Records ping results, latency, and status.
    """
    __tablename__ = "health_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=True)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # Target
    url = Column(String(500), nullable=False)
    method = Column(String(10), default="GET")
    
    # Results
    status = Column(String(20), default="unknown")  # healthy, degraded, unhealthy, unknown
    status_code = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    
    # Error info
    is_error = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    # Response details
    response_size_bytes = Column(Integer, nullable=True)
    headers = Column(JSON, nullable=True)
    
    # Timestamp
    checked_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    endpoint = relationship("APIEndpoint", backref="endpoint_health_checks")
    repository = relationship("Repository", backref="repo_health_checks")


class EndpointHealthSummary(Base):
    """
    Aggregated health summary per endpoint.
    Updated periodically for quick dashboard access.
    """
    __tablename__ = "endpoint_health_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Current status
    current_status = Column(String(20), default="unknown")
    last_checked_at = Column(DateTime, nullable=True)
    
    # Latency percentiles (last 24 hours)
    latency_p50 = Column(Float, nullable=True)
    latency_p95 = Column(Float, nullable=True)
    latency_p99 = Column(Float, nullable=True)
    latency_avg = Column(Float, nullable=True)
    
    # Uptime stats
    uptime_24h = Column(Float, default=100.0)  # Percentage
    uptime_7d = Column(Float, default=100.0)
    uptime_30d = Column(Float, default=100.0)
    
    # Check counts
    total_checks = Column(Integer, default=0)
    successful_checks = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)
    
    # Last status change
    last_status_change = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    endpoint = relationship("APIEndpoint", backref="health_summary", uselist=False)


class HealthAlert(Base):
    """
    Alert generated when health status changes.
    """
    __tablename__ = "health_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id", ondelete="SET NULL"), nullable=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # status_change, high_latency, downtime
    severity = Column(String(20), default="warning")  # info, warning, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    
    # Context
    previous_status = Column(String(20), nullable=True)
    current_status = Column(String(20), nullable=True)
    alert_metadata = Column(JSON, nullable=True)  # Additional context
    
    # Status
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    acknowledged_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="health_alerts")
    endpoint = relationship("APIEndpoint", backref="alerts")


class AlertConfig(Base):
    """
    Alert configuration for an organization or endpoint.
    """
    __tablename__ = "alert_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=True)  # Null = org-wide
    
    # Channel settings
    channel = Column(String(20), nullable=False)  # email, slack, pagerduty, webhook
    channel_config = Column(JSON, nullable=True)  # {"webhook_url": "...", "email": "..."}
    
    # Thresholds
    latency_threshold_ms = Column(Integer, default=1000)  # Alert if latency > this
    error_rate_threshold = Column(Float, default=5.0)  # Alert if error rate > this %
    downtime_threshold_minutes = Column(Integer, default=5)  # Alert if down > this
    
    # Alert types enabled
    alert_on_down = Column(Boolean, default=True)
    alert_on_degraded = Column(Boolean, default=True)
    alert_on_high_latency = Column(Boolean, default=True)
    alert_on_recovery = Column(Boolean, default=True)
    
    # Status
    is_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="alert_configs")


class HealthCheckSchedule(Base):
    """
    Schedule configuration for health checks.
    """
    __tablename__ = "health_check_schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # Schedule
    interval_seconds = Column(Integer, default=300)  # Default: 5 minutes
    is_active = Column(Boolean, default=True)
    
    # Check configuration
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    
    # Timestamps
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    
    # Relationships
    repository = relationship("Repository", backref="health_schedule", uselist=False)
