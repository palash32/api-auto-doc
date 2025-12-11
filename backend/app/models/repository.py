"""Repository and Git integration models."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Boolean, Integer

from app.core.db_utils import current_timestamp
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class GitProvider(str, PyEnum):
    """Supported Git providers."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class ScanStatus(str, PyEnum):
    """Repository scan status."""
    PENDING = "pending"
    SCANNING = "scanning"
    COMPLETED = "completed"
    FAILED = "failed"


class Repository(Base):
    """Connected Git repository."""
    
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Repository details
    name = Column(String(255), nullable=False)
    full_name = Column(String(500), nullable=False)  # e.g., "owner/repo"
    git_provider = Column(Enum(GitProvider), nullable=False)
    repo_url = Column(String(500), nullable=False)
    default_branch = Column(String(100), default="main", nullable=False)
    
    # Git provider integration
    provider_repo_id = Column(String(100), nullable=True)  # Repository ID from provider
    access_token_encrypted = Column(Text, nullable=True)  # Encrypted OAuth token
    
    # Scan information
    scan_status = Column(Enum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    last_scanned = Column(DateTime, nullable=True)
    last_commit_sha = Column(String(40), nullable=True)
    scan_error_message = Column(Text, nullable=True)
    
    # Statistics
    api_count = Column(Integer, default=0, nullable=False)
    
    # Settings
    auto_scan_enabled = Column(Boolean, default=True, nullable=False)  # Auto-scan on webhook
    scan_schedule = Column(String(50), nullable=True)  # Cron schedule for periodic scans
    
    # Timestamps
    created_at = Column(DateTime, default=current_timestamp, nullable=False)
    updated_at = Column(DateTime, default=current_timestamp, onupdate=current_timestamp)
    
    # Relationships
    organization = relationship("Organization", back_populates="repositories")
    api_endpoints = relationship("APIEndpoint", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository(id={self.id}, name='{self.full_name}')>"
