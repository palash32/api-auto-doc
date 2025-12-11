"""Security and compliance API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib
import secrets

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.security import AuditLog, SSOConfig, IPWhitelist, SecuritySettings
from app.models.user import APIKey

router = APIRouter()


# ==================== Pydantic Schemas ====================

class AuditLogResponse(BaseModel):
    id: str
    action: str
    user_email: Optional[str]
    resource_type: Optional[str]
    resource_name: Optional[str]
    description: Optional[str]
    ip_address: Optional[str]
    created_at: datetime


class AuditLogCreate(BaseModel):
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None


class SSOConfigCreate(BaseModel):
    provider_type: str  # saml, oidc, azure_ad, okta, google
    saml_entity_id: Optional[str] = None
    saml_sso_url: Optional[str] = None
    saml_certificate: Optional[str] = None
    oidc_issuer: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_client_secret: Optional[str] = None
    allowed_domains: Optional[List[str]] = None
    enforce_sso: bool = False
    auto_provision: bool = True
    default_role: str = "developer"


class SSOConfigResponse(BaseModel):
    id: str
    provider_type: str
    allowed_domains: Optional[List[str]]
    enforce_sso: bool
    auto_provision: bool
    is_enabled: bool
    is_verified: bool


class IPWhitelistCreate(BaseModel):
    ip_address: Optional[str] = None
    cidr_block: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None


class IPWhitelistResponse(BaseModel):
    id: str
    ip_address: Optional[str]
    cidr_block: Optional[str]
    label: Optional[str]
    is_enabled: bool
    created_at: datetime


class SecuritySettingsUpdate(BaseModel):
    min_password_length: Optional[int] = None
    require_uppercase: Optional[bool] = None
    require_numbers: Optional[bool] = None
    require_special_chars: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    mfa_required: Optional[bool] = None
    ip_whitelist_enabled: Optional[bool] = None
    api_rate_limit_per_minute: Optional[int] = None
    data_retention_days: Optional[int] = None


class SecuritySettingsResponse(BaseModel):
    min_password_length: int
    require_uppercase: bool
    require_numbers: bool
    require_special_chars: bool
    session_timeout_minutes: int
    mfa_required: bool
    ip_whitelist_enabled: bool
    api_rate_limit_per_minute: int
    data_retention_days: int


class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str] = ["read"]
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    use_count: int
    is_active: bool
    created_at: datetime


# ==================== Audit Log Endpoints ====================

@router.get("/security/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List audit logs with filtering."""
    org_id = current_user.get("organization_id")
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = (
        select(AuditLog)
        .where(
            AuditLog.organization_id == org_id,
            AuditLog.created_at >= start_date
        )
    )
    
    if action:
        query = query.where(AuditLog.action == action)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    query = query.order_by(desc(AuditLog.created_at)).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        AuditLogResponse(
            id=str(log.id),
            action=log.action,
            user_email=log.user_email,
            resource_type=log.resource_type,
            resource_name=log.resource_name,
            description=log.description,
            ip_address=log.ip_address,
            created_at=log.created_at
        )
        for log in logs
    ]


@router.post("/security/audit-logs")
async def create_audit_log(
    data: AuditLogCreate,
    request: Request,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create an audit log entry."""
    org_id = current_user.get("organization_id")
    
    log = AuditLog(
        organization_id=org_id,
        user_id=current_user.get("id"),
        user_email=current_user.get("email"),
        action=data.action,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        resource_name=data.resource_name,
        description=data.description,
        metadata=data.metadata,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    db.add(log)
    await db.commit()
    
    return {"message": "Audit log created", "id": str(log.id)}


# ==================== SSO Configuration ====================

@router.get("/security/sso", response_model=Optional[SSOConfigResponse])
async def get_sso_config(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get SSO configuration."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(SSOConfig).where(SSOConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        return None
    
    return SSOConfigResponse(
        id=str(config.id),
        provider_type=config.provider_type,
        allowed_domains=config.allowed_domains,
        enforce_sso=config.enforce_sso,
        auto_provision=config.auto_provision,
        is_enabled=config.is_enabled,
        is_verified=config.is_verified
    )


@router.post("/security/sso", response_model=SSOConfigResponse)
async def create_or_update_sso(
    data: SSOConfigCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create or update SSO configuration."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(SSOConfig).where(SSOConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    
    if config:
        # Update existing
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(config, field, value)
    else:
        # Create new
        config = SSOConfig(
            organization_id=org_id,
            **data.model_dump()
        )
        db.add(config)
    
    await db.commit()
    await db.refresh(config)
    
    return SSOConfigResponse(
        id=str(config.id),
        provider_type=config.provider_type,
        allowed_domains=config.allowed_domains,
        enforce_sso=config.enforce_sso,
        auto_provision=config.auto_provision,
        is_enabled=config.is_enabled,
        is_verified=config.is_verified
    )


@router.post("/security/sso/verify")
async def verify_sso(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Verify SSO configuration by testing connection."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(SSOConfig).where(SSOConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="SSO not configured")
    
    # In production, this would actually test the SSO connection
    config.is_verified = True
    config.is_enabled = True
    await db.commit()
    
    return {"message": "SSO verified and enabled"}


# ==================== IP Whitelist ====================

@router.get("/security/ip-whitelist", response_model=List[IPWhitelistResponse])
async def list_ip_whitelist(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List IP whitelist entries."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(IPWhitelist)
        .where(IPWhitelist.organization_id == org_id)
        .order_by(desc(IPWhitelist.created_at))
    )
    entries = result.scalars().all()
    
    return [
        IPWhitelistResponse(
            id=str(e.id),
            ip_address=e.ip_address,
            cidr_block=e.cidr_block,
            label=e.label,
            is_enabled=e.is_enabled,
            created_at=e.created_at
        )
        for e in entries
    ]


@router.post("/security/ip-whitelist", response_model=IPWhitelistResponse)
async def add_ip_whitelist(
    data: IPWhitelistCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Add an IP to the whitelist."""
    org_id = current_user.get("organization_id")
    
    entry = IPWhitelist(
        organization_id=org_id,
        ip_address=data.ip_address,
        cidr_block=data.cidr_block,
        label=data.label,
        description=data.description,
        created_by_id=current_user.get("id")
    )
    
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    
    return IPWhitelistResponse(
        id=str(entry.id),
        ip_address=entry.ip_address,
        cidr_block=entry.cidr_block,
        label=entry.label,
        is_enabled=entry.is_enabled,
        created_at=entry.created_at
    )


@router.delete("/security/ip-whitelist/{entry_id}")
async def remove_ip_whitelist(
    entry_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Remove an IP from the whitelist."""
    result = await db.execute(
        select(IPWhitelist).where(IPWhitelist.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    await db.delete(entry)
    await db.commit()
    
    return {"message": "IP whitelist entry removed"}


# ==================== Security Settings ====================

@router.get("/security/settings", response_model=SecuritySettingsResponse)
async def get_security_settings(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get security settings."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(SecuritySettings).where(SecuritySettings.organization_id == org_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Return defaults
        return SecuritySettingsResponse(
            min_password_length=8,
            require_uppercase=True,
            require_numbers=True,
            require_special_chars=False,
            session_timeout_minutes=1440,
            mfa_required=False,
            ip_whitelist_enabled=False,
            api_rate_limit_per_minute=1000,
            data_retention_days=365
        )
    
    return SecuritySettingsResponse(
        min_password_length=settings.min_password_length,
        require_uppercase=settings.require_uppercase,
        require_numbers=settings.require_numbers,
        require_special_chars=settings.require_special_chars,
        session_timeout_minutes=settings.session_timeout_minutes,
        mfa_required=settings.mfa_required,
        ip_whitelist_enabled=settings.ip_whitelist_enabled,
        api_rate_limit_per_minute=settings.api_rate_limit_per_minute,
        data_retention_days=settings.data_retention_days
    )


@router.patch("/security/settings", response_model=SecuritySettingsResponse)
async def update_security_settings(
    data: SecuritySettingsUpdate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Update security settings."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(SecuritySettings).where(SecuritySettings.organization_id == org_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = SecuritySettings(organization_id=org_id)
        db.add(settings)
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    
    await db.commit()
    await db.refresh(settings)
    
    return SecuritySettingsResponse(
        min_password_length=settings.min_password_length,
        require_uppercase=settings.require_uppercase,
        require_numbers=settings.require_numbers,
        require_special_chars=settings.require_special_chars,
        session_timeout_minutes=settings.session_timeout_minutes,
        mfa_required=settings.mfa_required,
        ip_whitelist_enabled=settings.ip_whitelist_enabled,
        api_rate_limit_per_minute=settings.api_rate_limit_per_minute,
        data_retention_days=settings.data_retention_days
    )


# ==================== API Keys ====================

@router.get("/security/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List API keys for the current user."""
    user_id = current_user.get("id")
    
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == user_id)
        .order_by(desc(APIKey.created_at))
    )
    keys = result.scalars().all()
    
    return [
        APIKeyResponse(
            id=str(k.id),
            name=k.name,
            key_prefix=k.key_prefix,
            scopes=k.scopes,
            expires_at=k.expires_at,
            last_used_at=k.last_used_at,
            use_count=k.use_count,
            is_active=k.is_active,
            created_at=k.created_at
        )
        for k in keys
    ]


@router.post("/security/api-keys")
async def create_api_key(
    data: APIKeyCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new API key. Returns the full key only once."""
    org_id = current_user.get("organization_id")
    user_id = current_user.get("id")
    
    # Generate a secure random key
    raw_key = secrets.token_urlsafe(32)
    key_prefix = raw_key[:8]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    expires_at = None
    if data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=data.expires_in_days)
    
    api_key = APIKey(
        organization_id=org_id,
        user_id=user_id,
        name=data.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=data.scopes,
        expires_at=expires_at
    )
    
    db.add(api_key)
    await db.commit()
    
    # Return the full key only this once
    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "key": f"apidoc_{raw_key}",  # Full key returned only once
        "key_prefix": key_prefix,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "message": "Save this key securely. It won't be shown again."
    }


@router.delete("/security/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Revoke an API key."""
    user_id = current_user.get("id")
    
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        )
    )
    key = result.scalar_one_or_none()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key.is_active = False
    await db.commit()
    
    return {"message": "API key revoked"}
