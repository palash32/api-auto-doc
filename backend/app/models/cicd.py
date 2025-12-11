"""CI/CD integration models for GitHub Actions, GitLab CI, Jenkins, and PR bots."""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
import enum

from app.core.database import Base


class CIProvider(enum.Enum):
    """CI/CD providers."""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    BITBUCKET = "bitbucket"
    CIRCLE_CI = "circle_ci"


class BuildStatus(enum.Enum):
    """Build statuses."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CIPipeline(Base):
    """
    CI/CD pipeline configuration.
    """
    __tablename__ = "ci_pipelines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # Provider
    provider = Column(String(30), nullable=False)  # github_actions, gitlab_ci, jenkins
    
    # Configuration
    name = Column(String(100), nullable=False)
    config_file = Column(String(200), nullable=True)  # .github/workflows/apidoc.yml
    
    # Triggers
    trigger_on_push = Column(Boolean, default=True)
    trigger_on_pr = Column(Boolean, default=True)
    trigger_branches = Column(JSON, default=["main", "master"])
    
    # Features
    auto_scan = Column(Boolean, default=True)
    pr_comments = Column(Boolean, default=True)
    fail_on_breaking_changes = Column(Boolean, default=False)
    
    # Status
    is_enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", backref="ci_pipelines")


class CIBuild(Base):
    """
    Individual CI build run.
    """
    __tablename__ = "ci_builds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pipeline_id = Column(String(36), ForeignKey("ci_pipelines.id", ondelete="CASCADE"), nullable=False)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # Build info
    build_number = Column(Integer, nullable=False)
    commit_sha = Column(String(40), nullable=True)
    branch = Column(String(100), nullable=True)
    
    # PR info
    pr_number = Column(Integer, nullable=True)
    pr_title = Column(String(200), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, running, success, failed
    
    # Results
    endpoints_found = Column(Integer, default=0)
    endpoints_added = Column(Integer, default=0)
    endpoints_modified = Column(Integer, default=0)
    endpoints_removed = Column(Integer, default=0)
    breaking_changes = Column(Integer, default=0)
    
    # Duration
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Logs
    log_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pipeline = relationship("CIPipeline", backref="builds")


class PRComment(Base):
    """
    Automated PR comment tracking.
    """
    __tablename__ = "pr_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    build_id = Column(String(36), ForeignKey("ci_builds.id", ondelete="SET NULL"), nullable=True)
    
    # PR info
    pr_number = Column(Integer, nullable=False)
    
    # Comment
    comment_id = Column(String(50), nullable=True)  # GitHub/GitLab comment ID
    content = Column(Text, nullable=True)
    
    # Summary
    summary = Column(JSON, nullable=True)  # {added: [], modified: [], removed: []}
    has_breaking_changes = Column(Boolean, default=False)
    
    # Status
    posted_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class BuildBadge(Base):
    """
    Build badges for repositories.
    """
    __tablename__ = "build_badges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Badge info
    badge_type = Column(String(20), default="status")  # status, coverage, endpoints
    
    # Current status
    status = Column(String(20), default="unknown")  # passing, failing, unknown
    label = Column(String(50), default="API Docs")
    message = Column(String(50), nullable=True)
    color = Column(String(20), default="blue")
    
    # Stats for badges
    endpoint_count = Column(Integer, default=0)
    coverage_percentage = Column(Float, nullable=True)
    
    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", backref="build_badge", uselist=False)


