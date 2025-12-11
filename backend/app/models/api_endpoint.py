"""API Endpoint model for discovered APIs."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, JSON, Boolean

from app.core.db_utils import current_timestamp
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class APIStatus(str, PyEnum):
    """API endpoint health status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


class HTTPMethod(str, PyEnum):
    """Supported HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class APIEndpoint(Base):
    """Discovered API endpoint from repository scan."""
    
    __tablename__ = "api_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Endpoint details
    path = Column(String(500), nullable=False, index=True)  # e.g., "/api/users/{id}"
    method = Column(String(10), nullable=False)  # GET, POST, etc.
    
    # Documentation (AI-generated or manual)
    summary = Column(String(500), nullable=False, default="")  # One-line description
    description = Column(Text, nullable=False, default="")  # Detailed explanation
    
    # OpenAPI/Swagger compatible fields
    tags = Column(JSON, nullable=False, default=list)  # ["users", "authentication"]
    parameters = Column(JSON, nullable=True)  # Parameter definitions
    request_body = Column(JSON, nullable=True)  # Request body schema
    responses = Column(JSON, nullable=True)  # Response schemas
    
    # Security
    auth_type = Column(String(50), nullable=True)  # "bearer", "api_key", "oauth2", None
    auth_required = Column(Boolean, default=False, nullable=False)
    
    # Health monitoring
    status = Column(String(20), default=APIStatus.UNKNOWN, nullable=False)
    latency_ms = Column(Integer, nullable=True)  # Average response time
    last_health_check = Column(DateTime, nullable=True)
    
    # Code location (for reference)
    file_path = Column(String(500), nullable=True)  # Path within repository
    line_number = Column(Integer, nullable=True)  # Line where endpoint is defined
    function_name = Column(String(255), nullable=True)  # Handler function name
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=current_timestamp, nullable=False, index=True)
    updated_at = Column(DateTime, default=current_timestamp, onupdate=current_timestamp, nullable=False)
    
    # Relationships
    repository = relationship("Repository", back_populates="api_endpoints")
    health_checks = relationship("APIHealthCheck", back_populates="api_endpoint", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<APIEndpoint(id={self.id}, method='{self.method}', path='{self.path}')>"
