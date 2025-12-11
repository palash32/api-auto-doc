"""Security and compliance models for audit logging, SSO, and access control."""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
import enum

from app.core.database import Base


class AuditAction(enum.Enum):
    """Audit action types."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_RESET = "password_reset"
    
    # User management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_INVITE = "user_invite"
    
    # Repository actions
    REPO_CREATE = "repo_create"
    REPO_UPDATE = "repo_update"
    REPO_DELETE = "repo_delete"
    REPO_SCAN = "repo_scan"
    
    # API documentation
    ENDPOINT_VIEW = "endpoint_view"
    ENDPOINT_UPDATE = "endpoint_update"
    DOCS_EXPORT = "docs_export"
    
    # Settings changes
    SETTINGS_UPDATE = "settings_update"
    SSO_CONFIG = "sso_config"
    ALERT_CONFIG = "alert_config"
    
    # Security events
    TOKEN_CREATE = "token_create"
    TOKEN_REVOKE = "token_revoke"
    IP_BLOCKED = "ip_blocked"
    PERMISSION_DENIED = "permission_denied"


class AuditLog(Base):
    """
    Comprehensive audit log for all security-relevant actions.
    SOC 2 Type II requires detailed audit trails.
    """
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Who
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(255), nullable=True)  # Store email in case user is deleted
    
    # What
    action = Column(String(50), nullable=False)  # From AuditAction enum
    resource_type = Column(String(50), nullable=True)  # repository, endpoint, user, etc.
    resource_id = Column(String(36), nullable=True)
    resource_name = Column(String(200), nullable=True)  # Human-readable name
    
    # Details
    description = Column(Text, nullable=True)
    old_value = Column(JSON, nullable=True)  # Before state
    new_value = Column(JSON, nullable=True)  # After state
    log_metadata = Column(JSON, nullable=True)  # Additional context
    
    # Where
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    country_code = Column(String(2), nullable=True)
    
    # When
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Status
    is_sensitive = Column(Boolean, default=False)  # Mark sensitive actions
    
    # Indexes for fast querying
    __table_args__ = (
        Index('idx_audit_org_time', 'organization_id', 'created_at'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
    )


class SSOConfig(Base):
    """
    SSO/SAML/OIDC configuration for an organization.
    """
    __tablename__ = "sso_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # SSO type
    provider_type = Column(String(20), nullable=False)  # saml, oidc, azure_ad, okta, google
    
    # SAML settings
    saml_entity_id = Column(String(500), nullable=True)
    saml_sso_url = Column(String(500), nullable=True)
    saml_certificate = Column(Text, nullable=True)
    saml_signature_algorithm = Column(String(50), default="SHA256")
    
    # OIDC settings
    oidc_issuer = Column(String(500), nullable=True)
    oidc_client_id = Column(String(200), nullable=True)
    oidc_client_secret = Column(String(500), nullable=True)  # Encrypted
    oidc_scopes = Column(String(200), default="openid profile email")
    
    # Domain settings
    allowed_domains = Column(JSON, nullable=True)  # ["company.com", "subsidiary.com"]
    enforce_sso = Column(Boolean, default=False)  # Block password login
    
    # User provisioning
    auto_provision = Column(Boolean, default=True)
    default_role = Column(String(50), default="developer")
    
    # Status
    is_enabled = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="sso_config", uselist=False)


class IPWhitelist(Base):
    """
    IP whitelisting rules for an organization.
    """
    __tablename__ = "ip_whitelists"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # IP rule
    ip_address = Column(String(45), nullable=True)  # Single IP
    ip_range_start = Column(String(45), nullable=True)  # Range start
    ip_range_end = Column(String(45), nullable=True)  # Range end
    cidr_block = Column(String(50), nullable=True)  # CIDR notation (e.g., 192.168.1.0/24)
    
    # Metadata
    label = Column(String(100), nullable=True)  # "Office Network", "VPN"
    description = Column(Text, nullable=True)
    
    # Status
    is_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", backref="ip_whitelists")


class SecuritySettings(Base):
    """
    Organization-wide security settings.
    """
    __tablename__ = "security_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Password policies
    min_password_length = Column(Integer, default=8)
    require_uppercase = Column(Boolean, default=True)
    require_lowercase = Column(Boolean, default=True)
    require_numbers = Column(Boolean, default=True)
    require_special_chars = Column(Boolean, default=False)
    password_expiry_days = Column(Integer, default=0)  # 0 = no expiry
    
    # Session settings
    session_timeout_minutes = Column(Integer, default=1440)  # 24 hours
    max_concurrent_sessions = Column(Integer, default=5)
    
    # MFA settings
    mfa_required = Column(Boolean, default=False)
    mfa_methods = Column(JSON, default=["totp"])  # totp, sms, email
    
    # IP restrictions
    ip_whitelist_enabled = Column(Boolean, default=False)
    block_tor_exit_nodes = Column(Boolean, default=False)
    
    # Data settings
    data_retention_days = Column(Integer, default=365)
    audit_log_retention_days = Column(Integer, default=365)
    
    # API security
    api_rate_limit_per_minute = Column(Integer, default=1000)
    require_api_key = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="security_settings", uselist=False)


class OrganizationAPIKey(Base):
    """
    API keys for programmatic access (organization-level).
    """
    __tablename__ = "org_api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Key details
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    key_hash = Column(String(64), nullable=False)  # SHA256 hash of full key
    
    # Permissions
    scopes = Column(JSON, default=["read"])  # read, write, admin
    
    # Restrictions
    allowed_ips = Column(JSON, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="org_api_keys")
    creator = relationship("User", backref="org_api_keys_created")
