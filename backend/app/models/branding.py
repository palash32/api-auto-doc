"""Custom branding models for white-label and customization features."""

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime

from app.core.database import Base


class OrganizationBranding(Base):
    """
    Custom branding settings for an organization.
    Enables white-labeling and custom theming.
    """
    __tablename__ = "organization_branding"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Logo settings
    logo_url = Column(String(500), nullable=True)  # Custom logo URL
    logo_dark_url = Column(String(500), nullable=True)  # Logo for dark mode
    favicon_url = Column(String(500), nullable=True)  # Custom favicon
    
    # Brand identity
    brand_name = Column(String(100), nullable=True)  # e.g., "Acme API Docs"
    tagline = Column(String(200), nullable=True)  # e.g., "Developer Portal"
    
    # Color scheme (hex values)
    primary_color = Column(String(20), default="#3B82F6")  # Primary brand color
    secondary_color = Column(String(20), nullable=True)
    accent_color = Column(String(20), nullable=True)
    background_color = Column(String(20), nullable=True)
    text_color = Column(String(20), nullable=True)
    
    # Theme settings
    theme_mode = Column(String(20), default="dark")  # light, dark, auto
    font_family = Column(String(100), nullable=True)  # Google Fonts name
    border_radius = Column(String(10), default="8px")  # UI corner radius
    
    # Custom CSS injection
    custom_css = Column(Text, nullable=True)  # Raw CSS for advanced customization
    
    # Custom JavaScript (for analytics, etc.)
    custom_head_scripts = Column(Text, nullable=True)  # Scripts for <head>
    custom_body_scripts = Column(Text, nullable=True)  # Scripts before </body>
    
    # Footer customization
    footer_text = Column(String(500), nullable=True)
    footer_links = Column(JSON, nullable=True)  # [{"label": "Terms", "url": "..."}]
    
    # Social links
    social_links = Column(JSON, nullable=True)  # {"twitter": "...", "github": "..."}
    
    # Feature flags
    hide_powered_by = Column(Boolean, default=False)  # Remove "Powered by" badge
    is_white_label = Column(Boolean, default=False)  # Full white-label mode
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="branding", uselist=False)


class CustomDomain(Base):
    """
    Custom domain configuration for documentation sites.
    Allows organizations to use their own domains.
    """
    __tablename__ = "custom_domains"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Domain settings
    domain = Column(String(255), nullable=False, unique=True)  # e.g., docs.acme.com
    subdomain = Column(String(100), nullable=True)  # If using our subdomain feature
    
    # SSL/TLS
    ssl_status = Column(String(20), default="pending")  # pending, active, failed
    ssl_expires_at = Column(DateTime, nullable=True)
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(100), nullable=True)  # DNS TXT record value
    verified_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)  # Primary domain for org
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="custom_domains")


class BrandingTemplate(Base):
    """
    Pre-built branding templates for quick setup.
    Organizations can start from a template and customize.
    """
    __tablename__ = "branding_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Template info
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    preview_url = Column(String(500), nullable=True)  # Screenshot/preview
    
    # Template settings (JSON)
    settings = Column(JSON, nullable=False)  # Full branding config
    
    # Categorization
    category = Column(String(50), nullable=True)  # tech, corporate, minimal, etc.
    is_premium = Column(Boolean, default=False)  # Premium tier only
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    use_count = Column(String(20), default="0")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
