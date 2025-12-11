"""Import/Export models for API documentation."""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
import enum

from app.core.database import Base


class ImportFormat(enum.Enum):
    """Supported import formats."""
    OPENAPI_30 = "openapi_3.0"
    OPENAPI_31 = "openapi_3.1"
    SWAGGER_20 = "swagger_2.0"
    POSTMAN_21 = "postman_2.1"
    INSOMNIA_4 = "insomnia_4"
    HAR = "har"


class ExportFormat(enum.Enum):
    """Supported export formats."""
    OPENAPI_30 = "openapi_3.0"
    POSTMAN_21 = "postman_2.1"
    INSOMNIA_4 = "insomnia_4"
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"


class ImportJob(Base):
    """
    Track import operations.
    """
    __tablename__ = "import_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # Import details
    format = Column(String(30), nullable=False)
    source_file = Column(String(500), nullable=True)
    source_url = Column(String(500), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    
    # Results
    endpoints_imported = Column(Integer, default=0)
    endpoints_updated = Column(Integer, default=0)
    endpoints_skipped = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)
    
    # Processing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships  
    repository = relationship("Repository", backref="import_jobs")


class ExportJob(Base):
    """
    Track export operations.
    """
    __tablename__ = "export_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    # Export details
    format = Column(String(30), nullable=False)
    include_examples = Column(Boolean, default=True)
    include_descriptions = Column(Boolean, default=True)
    
    # Customization
    title = Column(String(200), nullable=True)
    version = Column(String(50), nullable=True)
    base_url = Column(String(500), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    
    # Output
    output_url = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Processing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", backref="export_jobs")


class ExportTemplate(Base):
    """
    Custom export templates.
    """
    __tablename__ = "export_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Template details
    name = Column(String(100), nullable=False)
    format = Column(String(30), nullable=False)  # markdown, html
    
    # Template content
    header_template = Column(Text, nullable=True)
    endpoint_template = Column(Text, nullable=True)
    footer_template = Column(Text, nullable=True)
    
    # Styling (for HTML/PDF)
    css = Column(Text, nullable=True)
    
    # Status
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
