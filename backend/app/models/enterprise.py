"""Enterprise features models for self-hosted, SLA, support, and integrations."""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
import enum

from app.core.database import Base


class DeploymentType(enum.Enum):
    """Deployment types."""
    CLOUD = "cloud"
    SELF_HOSTED = "self_hosted"
    HYBRID = "hybrid"


class SupportTier(enum.Enum):
    """Support tiers."""
    COMMUNITY = "community"
    STANDARD = "standard"
    PRIORITY = "priority"
    DEDICATED = "dedicated"


class EnterpriseConfig(Base):
    """
    Enterprise configuration for an organization.
    """
    __tablename__ = "enterprise_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Deployment
    deployment_type = Column(String(20), default="cloud")  # cloud, self_hosted, hybrid
    instance_url = Column(String(500), nullable=True)  # For self-hosted
    license_key = Column(String(200), nullable=True)
    license_valid_until = Column(DateTime, nullable=True)
    
    # SLA
    sla_tier = Column(String(20), default="standard")  # standard, premium, enterprise
    uptime_sla = Column(Float, default=99.9)  # Percentage
    response_time_sla = Column(Integer, default=24)  # Hours
    
    # Support
    support_tier = Column(String(20), default="standard")
    support_email = Column(String(255), nullable=True)
    dedicated_success_manager = Column(String(200), nullable=True)
    slack_channel = Column(String(100), nullable=True)
    
    # Volume
    volume_discount_percentage = Column(Float, default=0)
    custom_contract = Column(Boolean, default=False)
    contract_end_date = Column(DateTime, nullable=True)
    
    # Features
    custom_features = Column(JSON, nullable=True)  # {"feature_name": True}
    feature_flags = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="enterprise_config", uselist=False)


class CustomIntegration(Base):
    """
    Custom integration configuration.
    """
    __tablename__ = "custom_integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Integration details
    name = Column(String(100), nullable=False)
    integration_type = Column(String(50), nullable=False)  # webhook, api, oauth, custom
    description = Column(Text, nullable=True)
    
    # Configuration
    config = Column(JSON, nullable=True)  # Integration-specific config
    credentials = Column(JSON, nullable=True)  # Encrypted credentials
    
    # Webhook settings
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(100), nullable=True)
    webhook_events = Column(JSON, nullable=True)  # ["endpoint_updated", "scan_complete"]
    
    # Status
    is_enabled = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="custom_integrations")


class SupportTicket(Base):
    """
    Enterprise support tickets.
    """
    __tablename__ = "support_tickets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Ticket details
    ticket_number = Column(String(20), nullable=False)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # technical, billing, feature_request
    
    # Priority
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Status
    status = Column(String(20), default="open")  # open, in_progress, waiting, resolved, closed
    
    # Assignment
    assigned_to = Column(String(200), nullable=True)
    
    # Resolution
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # SLA tracking
    sla_response_due = Column(DateTime, nullable=True)
    sla_resolution_due = Column(DateTime, nullable=True)
    sla_breached = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="support_tickets")
    user = relationship("User", backref="support_tickets")


class SLAMetric(Base):
    """
    Track SLA metrics for enterprise customers.
    """
    __tablename__ = "sla_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Uptime metrics
    uptime_percentage = Column(Float, nullable=True)
    total_downtime_minutes = Column(Integer, default=0)
    incidents_count = Column(Integer, default=0)
    
    # Response metrics
    avg_response_time_ms = Column(Float, nullable=True)
    p99_response_time_ms = Column(Float, nullable=True)
    
    # Support metrics
    tickets_opened = Column(Integer, default=0)
    tickets_resolved = Column(Integer, default=0)
    avg_resolution_hours = Column(Float, nullable=True)
    sla_breaches = Column(Integer, default=0)
    
    # Status
    sla_met = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
