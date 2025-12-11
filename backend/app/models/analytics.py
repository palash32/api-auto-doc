"""Analytics models for tracking API documentation usage and health."""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime, date

from app.core.database import Base


class EndpointView(Base):
    """
    Tracks individual endpoint views.
    Used for "most viewed endpoints" analytics.
    """
    __tablename__ = "endpoint_views"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False)
    
    # Viewer info (anonymized)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(100), nullable=True)  # Anonymous tracking
    
    # Request context
    ip_hash = Column(String(64), nullable=True)  # Hashed IP for unique visitor count
    user_agent = Column(String(255), nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # Timestamp
    viewed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    endpoint = relationship("APIEndpoint", backref="views")


class EndpointUsageStats(Base):
    """
    Aggregated daily usage statistics per endpoint.
    Pre-computed for fast dashboard queries.
    """
    __tablename__ = "endpoint_usage_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    
    # View counts
    view_count = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    
    # Engagement metrics
    avg_time_on_page = Column(Float, nullable=True)  # Seconds
    copy_code_count = Column(Integer, default=0)  # Code snippet copies
    try_it_count = Column(Integer, default=0)  # Playground usage
    
    # Traffic sources
    sources = Column(JSON, nullable=True)  # {"direct": 10, "search": 5, ...}
    
    # Relationships
    endpoint = relationship("APIEndpoint", backref="usage_stats")


class DocumentationHealth(Base):
    """
    Documentation health score per repository.
    Tracks completeness and quality metrics.
    """
    __tablename__ = "documentation_health"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Overall score (0-100)
    health_score = Column(Integer, default=0)
    
    # Component scores (0-100)
    description_coverage = Column(Integer, default=0)  # % endpoints with descriptions
    parameter_coverage = Column(Integer, default=0)   # % parameters documented
    response_coverage = Column(Integer, default=0)    # % responses documented
    example_coverage = Column(Integer, default=0)     # % with code examples
    
    # Detailed metrics
    total_endpoints = Column(Integer, default=0)
    documented_endpoints = Column(Integer, default=0)
    undocumented_endpoints = Column(Integer, default=0)
    deprecated_endpoints = Column(Integer, default=0)
    
    # Issues found
    issues = Column(JSON, nullable=True)  # [{"type": "missing_desc", "endpoint_id": "..."}]
    
    # Relationships
    repository = relationship("Repository", backref="health_scores")


class APILatencyMetric(Base):
    """
    API latency monitoring from playground tests.
    Tracks response times for performance insights.
    """
    __tablename__ = "api_latency_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=True)
    
    # Request details
    url = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    
    # Response metrics
    status_code = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=False)  # Response time in milliseconds
    response_size_bytes = Column(Integer, nullable=True)
    
    # Context
    tested_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    tested_at = Column(DateTime, default=datetime.utcnow)
    
    # Error tracking
    is_error = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    endpoint = relationship("APIEndpoint", backref="latency_metrics")


class AnalyticsSummary(Base):
    """
    Daily aggregated analytics summary per organization.
    For quick dashboard loading.
    """
    __tablename__ = "analytics_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Traffic metrics
    total_views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    
    # Documentation metrics
    total_endpoints = Column(Integer, default=0)
    avg_health_score = Column(Float, default=0)
    
    # Engagement
    playground_requests = Column(Integer, default=0)
    code_copies = Column(Integer, default=0)
    
    # Performance
    avg_latency_ms = Column(Float, nullable=True)
    error_rate = Column(Float, default=0)  # Percentage
    
    # Top items (JSON arrays)
    top_endpoints = Column(JSON, nullable=True)  # [{"id": "...", "views": 100}]
    top_referrers = Column(JSON, nullable=True)  # [{"source": "google", "count": 50}]
    
    # Relationships
    organization = relationship("Organization", backref="analytics_summaries")
