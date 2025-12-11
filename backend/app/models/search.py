"""Search and discovery models for full-text and semantic search."""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime

from app.core.database import Base


class SearchIndex(Base):
    """
    Search index for fast full-text search.
    Pre-computed searchable content for each endpoint.
    """
    __tablename__ = "search_indices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    endpoint_id = Column(UUID(as_uuid=True), ForeignKey("api_endpoints.id", ondelete="CASCADE"), nullable=False, unique=True)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Searchable content (combined for full-text search)
    search_content = Column(Text, nullable=False)  # Combined path + description + params
    
    # Individual fields for filtering
    path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    description = Column(Text, nullable=True)
    
    # Tags for filtering
    tags = Column(JSON, nullable=True)  # ["users", "auth", "public"]
    
    # Status flags
    is_deprecated = Column(Boolean, default=False)
    is_internal = Column(Boolean, default=False)
    
    # Computed relevance factors
    popularity_score = Column(Float, default=0)  # Based on views
    quality_score = Column(Float, default=0)  # Based on documentation completeness
    
    # Timestamps
    indexed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    endpoint = relationship("APIEndpoint", backref="search_index", uselist=False)
    
    # Indexes for fast search
    __table_args__ = (
        Index('idx_search_content', 'search_content'),
        Index('idx_search_method', 'method'),
        Index('idx_search_org', 'organization_id'),
    )


class SearchQuery(Base):
    """
    Track search queries for analytics and suggestions.
    """
    __tablename__ = "search_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Query details
    query_text = Column(String(500), nullable=False)
    query_type = Column(String(20), default="text")  # text, semantic, filter
    
    # Filters applied
    filters = Column(JSON, nullable=True)  # {"method": ["GET"], "tags": ["auth"]}
    
    # Results
    result_count = Column(Integer, default=0)
    clicked_result_id = Column(String(36), nullable=True)  # Which result was clicked
    
    # Context
    search_duration_ms = Column(Integer, nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Timestamp
    searched_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="search_queries")


class SavedSearch(Base):
    """
    User-saved search queries for quick access.
    """
    __tablename__ = "saved_searches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Search details
    name = Column(String(100), nullable=False)
    query_text = Column(String(500), nullable=True)
    filters = Column(JSON, nullable=True)
    
    # Settings
    is_pinned = Column(Boolean, default=False)
    notification_enabled = Column(Boolean, default=False)  # Alert on new matching endpoints
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", backref="saved_searches")


class SearchSuggestion(Base):
    """
    Pre-computed search suggestions based on popular queries.
    """
    __tablename__ = "search_suggestions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Suggestion content
    suggestion_text = Column(String(200), nullable=False)
    suggestion_type = Column(String(20), default="query")  # query, tag, path
    
    # Popularity
    use_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", backref="search_suggestions")
