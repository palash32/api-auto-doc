"""Version history and changelog models for tracking API changes."""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime

from app.core.database import Base


class APIVersion(Base):
    """
    Represents a specific version/snapshot of API documentation.
    Created on each scan or manual publish.
    """
    __tablename__ = "api_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # Version identification
    version = Column(String(50), nullable=False)  # e.g., "1.0.0", "2025-01-15"
    version_number = Column(Integer, nullable=False)  # Auto-increment for ordering
    
    # Git context
    commit_hash = Column(String(40), nullable=True)
    commit_message = Column(Text, nullable=True)
    branch = Column(String(100), nullable=True)
    
    # Version metadata
    title = Column(String(200), nullable=True)  # e.g., "Added user endpoints"
    description = Column(Text, nullable=True)
    
    # Full snapshot of endpoints at this version
    endpoints_snapshot = Column(JSON, nullable=True)  # [{path, method, description, ...}]
    
    # Stats
    total_endpoints = Column(Integer, default=0)
    added_endpoints = Column(Integer, default=0)
    modified_endpoints = Column(Integer, default=0)
    removed_endpoints = Column(Integer, default=0)
    
    # Status
    is_published = Column(Boolean, default=False)
    is_latest = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    repository = relationship("Repository", backref="versions")
    created_by = relationship("User", backref="created_versions")


class EndpointChange(Base):
    """
    Individual endpoint change between versions.
    Used for detailed changelog generation.
    """
    __tablename__ = "endpoint_changes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("api_versions.id", ondelete="CASCADE"), nullable=False)
    endpoint_id = Column(UUID(as_uuid=True), ForeignKey("api_endpoints.id", ondelete="SET NULL"), nullable=True)
    
    # Change type
    change_type = Column(String(20), nullable=False)  # added, modified, removed, deprecated
    
    # Endpoint identification
    path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    
    # Change details
    field_changed = Column(String(50), nullable=True)  # description, parameters, response, etc.
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    # Severity
    is_breaking = Column(Boolean, default=False)
    severity = Column(String(20), default="low")  # low, medium, high
    
    # Human-readable description
    description = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    version = relationship("APIVersion", backref="changes")
    endpoint = relationship("APIEndpoint", backref="history")


class Changelog(Base):
    """
    Generated changelog for a version.
    Can be customized before publishing.
    """
    __tablename__ = "changelogs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("api_versions.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Changelog content
    content_markdown = Column(Text, nullable=True)  # Markdown formatted changelog
    content_html = Column(Text, nullable=True)  # Rendered HTML
    
    # Sections
    breaking_changes = Column(JSON, nullable=True)  # [{description, path, method}]
    new_endpoints = Column(JSON, nullable=True)
    modified_endpoints = Column(JSON, nullable=True)
    deprecated_endpoints = Column(JSON, nullable=True)
    removed_endpoints = Column(JSON, nullable=True)
    
    # Status
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    version = relationship("APIVersion", backref="changelog", uselist=False)


class VersionBookmark(Base):
    """
    User bookmark for specific API versions.
    Enables quick access and comparison.
    """
    __tablename__ = "version_bookmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version_id = Column(UUID(as_uuid=True), ForeignKey("api_versions.id", ondelete="CASCADE"), nullable=False)
    
    # Bookmark metadata
    label = Column(String(100), nullable=True)  # Custom label
    notes = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="version_bookmarks")
    version = relationship("APIVersion", backref="bookmarks")
