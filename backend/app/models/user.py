"""User and Organization models."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Enum

from app.core.db_utils import current_timestamp
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, PyEnum):
    """User roles for RBAC."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class SubscriptionTier(str, PyEnum):
    """Organization subscription tiers."""
    FREE = "free"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class Organization(Base):
    """Organization/company that uses the platform."""
    
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=False, index=True)
    subscription_tier = Column(
        Enum(SubscriptionTier),
        default=SubscriptionTier.FREE,
        nullable=False
    )
    developer_count = Column(Integer, default=1, nullable=False)
    
    # Stripe integration
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=current_timestamp, nullable=False)
    updated_at = Column(DateTime, default=current_timestamp, onupdate=current_timestamp)
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    repositories = relationship("Repository", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"


class User(Base):
    """User account."""
    
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Organization membership
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.DEVELOPER, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=current_timestamp, nullable=False)
    updated_at = Column(DateTime, default=current_timestamp, onupdate=current_timestamp)
    last_login = Column(DateTime, nullable=True)
    
    # OAuth provider IDs (for reliable user lookup)
    github_id = Column(String(50), unique=True, nullable=True, index=True)  # GitHub numeric user ID
    github_username = Column(String(100), nullable=True)  # GitHub login username
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    # Playground relationships
    playground_tokens = relationship("PlaygroundToken", back_populates="user", cascade="all, delete-orphan")
    playground_environments = relationship("PlaygroundEnvironment", back_populates="user", cascade="all, delete-orphan")
    playground_requests = relationship("PlaygroundRequest", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class APIKey(Base):
    """API keys for programmatic access."""
    
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)  # User-friendly name
    key_hash = Column(String(255), nullable=False)  # Hashed API key
    key_prefix = Column(String(20), nullable=False, index=True)  # For identification
    
    # Permissions and limits
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=current_timestamp, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"
