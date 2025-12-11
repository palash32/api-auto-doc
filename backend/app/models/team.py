"""Team collaboration models for multi-user access control."""

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from enum import Enum

from app.core.database import Base


class TeamRole(str, Enum):
    """Team member roles with hierarchical permissions."""
    OWNER = "owner"        # Full control, can delete org
    ADMIN = "admin"        # Can manage members, settings
    DEVELOPER = "developer"  # Can edit docs, run scans
    VIEWER = "viewer"      # Read-only access


class ChangeStatus(str, Enum):
    """Status of a documentation change request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


class TeamMember(Base):
    """
    Team member with role-based access control.
    Links users to organizations with specific permissions.
    """
    __tablename__ = "team_members"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Role and permissions
    role = Column(String(20), default=TeamRole.VIEWER.value, nullable=False)
    
    # Invitation tracking
    invited_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    invited_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="team_memberships")
    organization = relationship("Organization", backref="team_members")
    
    def has_permission(self, permission: str) -> bool:
        """Check if member has a specific permission."""
        permissions = {
            TeamRole.OWNER.value: ["read", "write", "delete", "manage_members", "manage_settings", "delete_org"],
            TeamRole.ADMIN.value: ["read", "write", "delete", "manage_members", "manage_settings"],
            TeamRole.DEVELOPER.value: ["read", "write", "run_scans"],
            TeamRole.VIEWER.value: ["read"]
        }
        return permission in permissions.get(self.role, [])


class Workspace(Base):
    """
    Workspace for organizing projects within an organization.
    Allows logical grouping of repositories and documentation.
    """
    __tablename__ = "workspaces"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Workspace details
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)  # URL-friendly identifier
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Emoji or icon name
    color = Column(String(20), nullable=True)  # Hex color
    
    # Settings
    is_default = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)  # Only visible to assigned members
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", backref="workspaces")
    created_by = relationship("User", backref="created_workspaces")


class WorkspaceMember(Base):
    """
    Links team members to specific workspaces.
    Allows fine-grained access control per workspace.
    """
    __tablename__ = "workspace_members"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Workspace-specific role (override team role if needed)
    role = Column(String(20), nullable=True)  # Null = inherit from team role
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", backref="members")
    user = relationship("User", backref="workspace_memberships")


class EndpointComment(Base):
    """
    Comments and annotations on API endpoints.
    Supports threaded discussions.
    """
    __tablename__ = "endpoint_comments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Threading support
    parent_id = Column(String(36), ForeignKey("endpoint_comments.id", ondelete="CASCADE"), nullable=True)
    
    # Line-specific annotation
    line_number = Column(String(10), nullable=True)  # Can be range like "10-15"
    
    # Status
    is_resolved = Column(Boolean, default=False)
    resolved_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    endpoint = relationship("APIEndpoint", backref="comments")
    user = relationship("User", foreign_keys=[user_id], backref="endpoint_comments")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    replies = relationship("EndpointComment", backref="parent", remote_side=[id])


class ChangeRequest(Base):
    """
    Change request for documentation updates requiring approval.
    Implements a simple review workflow.
    """
    __tablename__ = "change_requests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Change details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # The proposed changes (JSON diff format)
    changes = Column(JSON, nullable=False)  # {"field": {"old": x, "new": y}}
    
    # Status
    status = Column(String(20), default=ChangeStatus.PENDING.value)
    
    # Review
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comment = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    endpoint = relationship("APIEndpoint", backref="change_requests")
    author = relationship("User", foreign_keys=[author_id], backref="authored_changes")
    reviewer = relationship("User", foreign_keys=[reviewer_id], backref="reviewed_changes")


class ActivityLog(Base):
    """
    Audit log for team activity tracking.
    Records all significant actions for compliance.
    """
    __tablename__ = "activity_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Activity details
    action = Column(String(50), nullable=False)  # e.g., "endpoint.updated", "member.invited"
    resource_type = Column(String(50), nullable=True)  # e.g., "endpoint", "repository"
    resource_id = Column(String(36), nullable=True)
    
    # Additional context
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="activity_logs")
    user = relationship("User", backref="activity_logs")
