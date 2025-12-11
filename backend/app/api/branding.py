"""Custom branding API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel
from datetime import datetime
import secrets

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.branding import OrganizationBranding, CustomDomain, BrandingTemplate

router = APIRouter()


# ==================== Pydantic Schemas ====================

class BrandingUpdate(BaseModel):
    # Logo
    logo_url: Optional[str] = None
    logo_dark_url: Optional[str] = None
    favicon_url: Optional[str] = None
    
    # Brand identity
    brand_name: Optional[str] = None
    tagline: Optional[str] = None
    
    # Colors
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    
    # Theme
    theme_mode: Optional[str] = None
    font_family: Optional[str] = None
    border_radius: Optional[str] = None
    
    # Custom code
    custom_css: Optional[str] = None
    custom_head_scripts: Optional[str] = None
    custom_body_scripts: Optional[str] = None
    
    # Footer
    footer_text: Optional[str] = None
    footer_links: Optional[List[dict]] = None
    social_links: Optional[dict] = None
    
    # White-label
    hide_powered_by: Optional[bool] = None
    is_white_label: Optional[bool] = None


class BrandingResponse(BaseModel):
    id: str
    organization_id: str
    logo_url: Optional[str]
    logo_dark_url: Optional[str]
    favicon_url: Optional[str]
    brand_name: Optional[str]
    tagline: Optional[str]
    primary_color: str
    secondary_color: Optional[str]
    accent_color: Optional[str]
    background_color: Optional[str]
    text_color: Optional[str]
    theme_mode: str
    font_family: Optional[str]
    border_radius: str
    custom_css: Optional[str]
    footer_text: Optional[str]
    footer_links: Optional[List[dict]]
    social_links: Optional[dict]
    hide_powered_by: bool
    is_white_label: bool
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DomainCreate(BaseModel):
    domain: str


class DomainResponse(BaseModel):
    id: str
    domain: str
    ssl_status: str
    is_verified: bool
    is_active: bool
    is_primary: bool
    verification_token: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    preview_url: Optional[str]
    category: Optional[str]
    is_premium: bool
    settings: dict
    
    class Config:
        from_attributes = True


# ==================== Branding Endpoints ====================

@router.get("/branding", response_model=BrandingResponse)
async def get_branding(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get organization branding settings."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(OrganizationBranding).where(OrganizationBranding.organization_id == org_id)
    )
    branding = result.scalar_one_or_none()
    
    # Create default branding if none exists
    if not branding:
        branding = OrganizationBranding(
            organization_id=org_id
        )
        db.add(branding)
        await db.commit()
        await db.refresh(branding)
    
    return BrandingResponse(
        id=str(branding.id),
        organization_id=str(branding.organization_id),
        logo_url=branding.logo_url,
        logo_dark_url=branding.logo_dark_url,
        favicon_url=branding.favicon_url,
        brand_name=branding.brand_name,
        tagline=branding.tagline,
        primary_color=branding.primary_color,
        secondary_color=branding.secondary_color,
        accent_color=branding.accent_color,
        background_color=branding.background_color,
        text_color=branding.text_color,
        theme_mode=branding.theme_mode,
        font_family=branding.font_family,
        border_radius=branding.border_radius,
        custom_css=branding.custom_css,
        footer_text=branding.footer_text,
        footer_links=branding.footer_links,
        social_links=branding.social_links,
        hide_powered_by=branding.hide_powered_by,
        is_white_label=branding.is_white_label,
        updated_at=branding.updated_at
    )


@router.patch("/branding", response_model=BrandingResponse)
async def update_branding(
    data: BrandingUpdate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Update organization branding settings."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(OrganizationBranding).where(OrganizationBranding.organization_id == org_id)
    )
    branding = result.scalar_one_or_none()
    
    if not branding:
        branding = OrganizationBranding(organization_id=org_id)
        db.add(branding)
    
    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(branding, field):
            setattr(branding, field, value)
    
    await db.commit()
    await db.refresh(branding)
    
    return BrandingResponse(
        id=str(branding.id),
        organization_id=str(branding.organization_id),
        logo_url=branding.logo_url,
        logo_dark_url=branding.logo_dark_url,
        favicon_url=branding.favicon_url,
        brand_name=branding.brand_name,
        tagline=branding.tagline,
        primary_color=branding.primary_color,
        secondary_color=branding.secondary_color,
        accent_color=branding.accent_color,
        background_color=branding.background_color,
        text_color=branding.text_color,
        theme_mode=branding.theme_mode,
        font_family=branding.font_family,
        border_radius=branding.border_radius,
        custom_css=branding.custom_css,
        footer_text=branding.footer_text,
        footer_links=branding.footer_links,
        social_links=branding.social_links,
        hide_powered_by=branding.hide_powered_by,
        is_white_label=branding.is_white_label,
        updated_at=branding.updated_at
    )


@router.post("/branding/reset")
async def reset_branding(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Reset branding to defaults."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(OrganizationBranding).where(OrganizationBranding.organization_id == org_id)
    )
    branding = result.scalar_one_or_none()
    
    if branding:
        # Reset to defaults
        branding.logo_url = None
        branding.logo_dark_url = None
        branding.brand_name = None
        branding.tagline = None
        branding.primary_color = "#3B82F6"
        branding.secondary_color = None
        branding.accent_color = None
        branding.theme_mode = "dark"
        branding.custom_css = None
        branding.hide_powered_by = False
        branding.is_white_label = False
        
        await db.commit()
    
    return {"message": "Branding reset to defaults"}


# ==================== Custom Domain Endpoints ====================

@router.get("/domains", response_model=List[DomainResponse])
async def list_domains(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List custom domains for the organization."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(CustomDomain).where(CustomDomain.organization_id == org_id)
    )
    domains = result.scalars().all()
    
    return [
        DomainResponse(
            id=str(d.id),
            domain=d.domain,
            ssl_status=d.ssl_status,
            is_verified=d.is_verified,
            is_active=d.is_active,
            is_primary=d.is_primary,
            verification_token=d.verification_token,
            created_at=d.created_at
        )
        for d in domains
    ]


@router.post("/domains", response_model=DomainResponse)
async def add_domain(
    data: DomainCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Add a custom domain."""
    org_id = current_user.get("organization_id")
    
    # Check if domain already exists
    existing = await db.execute(
        select(CustomDomain).where(CustomDomain.domain == data.domain)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Domain already registered")
    
    # Generate verification token
    verification_token = f"api-docs-verify-{secrets.token_hex(16)}"
    
    domain = CustomDomain(
        organization_id=org_id,
        domain=data.domain,
        verification_token=verification_token
    )
    
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    
    return DomainResponse(
        id=str(domain.id),
        domain=domain.domain,
        ssl_status=domain.ssl_status,
        is_verified=domain.is_verified,
        is_active=domain.is_active,
        is_primary=domain.is_primary,
        verification_token=domain.verification_token,
        created_at=domain.created_at
    )


@router.post("/domains/{domain_id}/verify")
async def verify_domain(
    domain_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Verify domain ownership via DNS TXT record.
    User should add TXT record: _api-docs-verify.domain.com = {verification_token}
    """
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(CustomDomain).where(
            CustomDomain.id == domain_id,
            CustomDomain.organization_id == org_id
        )
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # In production, implement DNS TXT record lookup
    # For now, auto-verify for development
    domain.is_verified = True
    domain.is_active = True
    domain.verified_at = datetime.utcnow()
    domain.ssl_status = "active"
    
    await db.commit()
    
    return {"message": "Domain verified and activated", "domain": domain.domain}


@router.delete("/domains/{domain_id}")
async def remove_domain(
    domain_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Remove a custom domain."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(CustomDomain).where(
            CustomDomain.id == domain_id,
            CustomDomain.organization_id == org_id
        )
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    await db.delete(domain)
    await db.commit()
    
    return {"message": "Domain removed"}


# ==================== Template Endpoints ====================

@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """List available branding templates."""
    query = select(BrandingTemplate).where(BrandingTemplate.is_active == True)
    
    if category:
        query = query.where(BrandingTemplate.category == category)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [
        TemplateResponse(
            id=str(t.id),
            name=t.name,
            description=t.description,
            preview_url=t.preview_url,
            category=t.category,
            is_premium=t.is_premium,
            settings=t.settings
        )
        for t in templates
    ]


@router.post("/templates/{template_id}/apply")
async def apply_template(
    template_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Apply a branding template to the organization."""
    org_id = current_user.get("organization_id")
    
    # Get template
    result = await db.execute(
        select(BrandingTemplate).where(BrandingTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get or create branding
    result = await db.execute(
        select(OrganizationBranding).where(OrganizationBranding.organization_id == org_id)
    )
    branding = result.scalar_one_or_none()
    
    if not branding:
        branding = OrganizationBranding(organization_id=org_id)
        db.add(branding)
    
    # Apply template settings
    settings = template.settings
    for field, value in settings.items():
        if hasattr(branding, field):
            setattr(branding, field, value)
    
    # Update template usage count
    template.use_count = str(int(template.use_count or "0") + 1)
    
    await db.commit()
    
    return {"message": f"Template '{template.name}' applied successfully"}


# ==================== CSS Generator ====================

@router.get("/css")
async def generate_css(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Generate CSS variables based on branding settings."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(OrganizationBranding).where(OrganizationBranding.organization_id == org_id)
    )
    branding = result.scalar_one_or_none()
    
    # Default values
    primary = branding.primary_color if branding else "#3B82F6"
    secondary = branding.secondary_color if branding else "#6366F1"
    accent = branding.accent_color if branding else "#10B981"
    bg = branding.background_color if branding else "#0A0A0A"
    text = branding.text_color if branding else "#FFFFFF"
    radius = branding.border_radius if branding else "8px"
    font = branding.font_family if branding else "Inter, system-ui, sans-serif"
    
    css = f"""
:root {{
  --brand-primary: {primary};
  --brand-secondary: {secondary or primary};
  --brand-accent: {accent or primary};
  --brand-background: {bg};
  --brand-text: {text};
  --brand-radius: {radius};
  --brand-font: {font};
}}

/* Apply branding */
body {{
  background-color: var(--brand-background);
  color: var(--brand-text);
  font-family: var(--brand-font);
}}

.btn-primary {{
  background-color: var(--brand-primary);
}}

.card {{
  border-radius: var(--brand-radius);
}}
"""
    
    # Add custom CSS if present
    if branding and branding.custom_css:
        css += f"\n/* Custom CSS */\n{branding.custom_css}"
    
    return JSONResponse(
        content={"css": css},
        media_type="application/json"
    )
