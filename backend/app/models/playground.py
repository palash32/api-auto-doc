"""Models for the API Playground feature - Auth tokens and environments."""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class PlaygroundToken(Base):
    """Secure storage for API tokens used in the playground."""
    __tablename__ = "playground_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Token details
    name = Column(String(100), nullable=False)  # e.g., "Production API Key"
    token_type = Column(String(50), nullable=False, default="bearer")  # bearer, api_key, basic
    encrypted_value = Column(Text, nullable=False)  # Encrypted token value
    
    # Optional metadata
    prefix = Column(String(20), nullable=True)  # For display: "sk-...xxxx"
    expires_at = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(String(10), default="0")  # How many times used
    
    # Relationships
    user = relationship("User", back_populates="playground_tokens")


class PlaygroundEnvironment(Base):
    """Environment variables for API playground (dev, staging, prod)."""
    __tablename__ = "playground_environments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(50), nullable=False)  # e.g., "Development", "Production"
    is_default = Column(Boolean, default=False)
    
    # Variables stored as encrypted JSON
    variables = Column(JSON, nullable=False, default=dict)  # {"BASE_URL": "...", "API_VERSION": "v1"}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="playground_environments")


class PlaygroundRequest(Base):
    """Request history for the API playground."""
    __tablename__ = "playground_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Request details
    method = Column(String(10), nullable=False)  # GET, POST, etc.
    url = Column(Text, nullable=False)
    headers = Column(JSON, default=dict)
    body = Column(Text, nullable=True)
    
    # Response details (optional, for history)
    response_status = Column(String(10), nullable=True)
    response_time_ms = Column(String(20), nullable=True)
    
    # Metadata
    name = Column(String(100), nullable=True)  # Optional saved name
    is_saved = Column(Boolean, default=False)  # Favorited/saved request
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="playground_requests")
