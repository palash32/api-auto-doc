"""API health monitoring and metrics models."""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Date, Text, Float, Boolean

from app.core.db_utils import current_timestamp
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class APIHealthCheck(Base):
    """Individual health check result for an API endpoint."""
    
    __tablename__ = "api_health_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_endpoint_id = Column(UUID(as_uuid=True), ForeignKey("api_endpoints.id"), nullable=False)
    
    # Check results
    status_code = Column(Integer, nullable=True)  # HTTP status code
    response_time_ms = Column(Float, nullable=True)  # Response time in milliseconds
    is_healthy = Column(Boolean, default=True, nullable=False)  # Overall health status
    error_message = Column(Text, nullable=True)  # Error details if failed
    
    # Timestamp
    checked_at = Column(DateTime, default=current_timestamp, nullable=False, index=True)
    
    # Relationships
    api_endpoint = relationship("APIEndpoint", back_populates="health_checks")

    def __repr__(self):
        return f"<APIHealthCheck(id={self.id}, status={self.status_code}, time={self.response_time_ms}ms)>"


class APIMetrics(Base):
    """Aggregated daily metrics for an API endpoint."""
    
    __tablename__ = "api_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_endpoint_id = Column(UUID(as_uuid=True), ForeignKey("api_endpoints.id"), nullable=False)
    
    # Date for these metrics
    date = Column(Date, nullable=False, index=True)
    
    # Aggregated statistics
    total_calls = Column(Integer, default=0, nullable=False)
    total_errors = Column(Integer, default=0, nullable=False)
    avg_response_time = Column(Float, nullable=True)  # Average response time in ms
    min_response_time = Column(Float, nullable=True)
    max_response_time = Column(Float, nullable=True)
    p95_response_time = Column(Float, nullable=True)  # 95th percentile
    p99_response_time = Column(Float, nullable=True)  # 99th percentile
    
    # Availability
    uptime_percentage = Column(Float, default=100.0, nullable=False)
    downtime_minutes = Column(Integer, default=0, nullable=False)
    
    # Error rates
    error_rate = Column(Float, default=0.0, nullable=False)  # Percentage of failed requests
    
    # Timestamp
    created_at = Column(DateTime, default=current_timestamp, nullable=False)
    
    # Relationships
    api_endpoint = relationship("APIEndpoint")

    def __repr__(self):
        return f"<APIMetrics(endpoint={self.api_endpoint_id}, date={self.date})>"
