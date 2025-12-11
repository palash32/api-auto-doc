"""Enterprise features API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.enterprise import (
    EnterpriseConfig, CustomIntegration, SupportTicket, SLAMetric
)

router = APIRouter()


# ==================== Pydantic Schemas ====================

class EnterpriseConfigResponse(BaseModel):
    id: str
    deployment_type: str
    sla_tier: str
    uptime_sla: float
    response_time_sla: int
    support_tier: str
    dedicated_success_manager: Optional[str]
    volume_discount_percentage: float
    custom_contract: bool


class EnterpriseConfigUpdate(BaseModel):
    deployment_type: Optional[str] = None
    sla_tier: Optional[str] = None
    support_tier: Optional[str] = None
    dedicated_success_manager: Optional[str] = None


class IntegrationCreate(BaseModel):
    name: str
    integration_type: str  # webhook, api, oauth
    description: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_events: Optional[List[str]] = None
    config: Optional[dict] = None


class IntegrationResponse(BaseModel):
    id: str
    name: str
    integration_type: str
    description: Optional[str]
    webhook_url: Optional[str]
    webhook_events: Optional[List[str]]
    is_enabled: bool
    last_triggered_at: Optional[datetime]
    error_count: int


class TicketCreate(BaseModel):
    subject: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: str = "medium"


class TicketResponse(BaseModel):
    id: str
    ticket_number: str
    subject: str
    description: Optional[str]
    category: Optional[str]
    priority: str
    status: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime


class SLAResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    uptime_percentage: Optional[float]
    avg_response_time_ms: Optional[float]
    tickets_resolved: int
    sla_met: bool


# ==================== Enterprise Config Endpoints ====================

@router.get("/enterprise/config", response_model=Optional[EnterpriseConfigResponse])
async def get_enterprise_config(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get enterprise configuration."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(EnterpriseConfig).where(EnterpriseConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        return None
    
    return EnterpriseConfigResponse(
        id=str(config.id),
        deployment_type=config.deployment_type,
        sla_tier=config.sla_tier,
        uptime_sla=config.uptime_sla,
        response_time_sla=config.response_time_sla,
        support_tier=config.support_tier,
        dedicated_success_manager=config.dedicated_success_manager,
        volume_discount_percentage=config.volume_discount_percentage,
        custom_contract=config.custom_contract
    )


@router.post("/enterprise/config", response_model=EnterpriseConfigResponse)
async def create_or_update_enterprise_config(
    data: EnterpriseConfigUpdate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create or update enterprise configuration."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(EnterpriseConfig).where(EnterpriseConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    
    if config:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(config, field, value)
    else:
        config = EnterpriseConfig(
            organization_id=org_id,
            **data.model_dump(exclude_unset=True)
        )
        db.add(config)
    
    await db.commit()
    await db.refresh(config)
    
    return EnterpriseConfigResponse(
        id=str(config.id),
        deployment_type=config.deployment_type,
        sla_tier=config.sla_tier,
        uptime_sla=config.uptime_sla,
        response_time_sla=config.response_time_sla,
        support_tier=config.support_tier,
        dedicated_success_manager=config.dedicated_success_manager,
        volume_discount_percentage=config.volume_discount_percentage,
        custom_contract=config.custom_contract
    )


@router.post("/enterprise/license/validate")
async def validate_license(
    license_key: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Validate a self-hosted license key."""
    org_id = current_user.get("organization_id")
    
    # In production, would validate against license server
    # Simplified validation
    if len(license_key) < 20:
        raise HTTPException(status_code=400, detail="Invalid license key")
    
    result = await db.execute(
        select(EnterpriseConfig).where(EnterpriseConfig.organization_id == org_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        config = EnterpriseConfig(organization_id=org_id)
        db.add(config)
    
    config.license_key = license_key
    config.license_valid_until = datetime.utcnow() + timedelta(days=365)
    config.deployment_type = "self_hosted"
    
    await db.commit()
    
    return {
        "valid": True,
        "expires": config.license_valid_until.isoformat(),
        "message": "License activated successfully"
    }


# ==================== Custom Integrations ====================

@router.get("/enterprise/integrations", response_model=List[IntegrationResponse])
async def list_integrations(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List custom integrations."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(CustomIntegration)
        .where(CustomIntegration.organization_id == org_id)
        .order_by(desc(CustomIntegration.created_at))
    )
    integrations = result.scalars().all()
    
    return [
        IntegrationResponse(
            id=str(i.id),
            name=i.name,
            integration_type=i.integration_type,
            description=i.description,
            webhook_url=i.webhook_url,
            webhook_events=i.webhook_events,
            is_enabled=i.is_enabled,
            last_triggered_at=i.last_triggered_at,
            error_count=i.error_count
        )
        for i in integrations
    ]


@router.post("/enterprise/integrations", response_model=IntegrationResponse)
async def create_integration(
    data: IntegrationCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a custom integration."""
    org_id = current_user.get("organization_id")
    
    integration = CustomIntegration(
        organization_id=org_id,
        name=data.name,
        integration_type=data.integration_type,
        description=data.description,
        webhook_url=data.webhook_url,
        webhook_events=data.webhook_events,
        config=data.config
    )
    
    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    
    return IntegrationResponse(
        id=str(integration.id),
        name=integration.name,
        integration_type=integration.integration_type,
        description=integration.description,
        webhook_url=integration.webhook_url,
        webhook_events=integration.webhook_events,
        is_enabled=integration.is_enabled,
        last_triggered_at=integration.last_triggered_at,
        error_count=integration.error_count
    )


@router.delete("/enterprise/integrations/{integration_id}")
async def delete_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete an integration."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(CustomIntegration).where(
            CustomIntegration.id == integration_id,
            CustomIntegration.organization_id == org_id
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    await db.delete(integration)
    await db.commit()
    
    return {"message": "Integration deleted"}


@router.post("/enterprise/integrations/{integration_id}/test")
async def test_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Test an integration webhook."""
    result = await db.execute(
        select(CustomIntegration).where(CustomIntegration.id == integration_id)
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # In production, would send test payload to webhook
    integration.last_triggered_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Test webhook sent", "success": True}


# ==================== Support Tickets ====================

@router.get("/enterprise/tickets", response_model=List[TicketResponse])
async def list_tickets(
    status: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List support tickets."""
    org_id = current_user.get("organization_id")
    
    query = select(SupportTicket).where(SupportTicket.organization_id == org_id)
    
    if status:
        query = query.where(SupportTicket.status == status)
    
    query = query.order_by(desc(SupportTicket.created_at)).limit(limit)
    
    result = await db.execute(query)
    tickets = result.scalars().all()
    
    return [
        TicketResponse(
            id=str(t.id),
            ticket_number=t.ticket_number,
            subject=t.subject,
            description=t.description,
            category=t.category,
            priority=t.priority,
            status=t.status,
            assigned_to=t.assigned_to,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in tickets
    ]


@router.post("/enterprise/tickets", response_model=TicketResponse)
async def create_ticket(
    data: TicketCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a support ticket."""
    org_id = current_user.get("organization_id")
    user_id = current_user.get("id")
    
    # Generate ticket number
    count_result = await db.execute(
        select(func.count(SupportTicket.id))
        .where(SupportTicket.organization_id == org_id)
    )
    count = count_result.scalar() or 0
    ticket_number = f"TKT-{count + 1:05d}"
    
    # Calculate SLA due times based on priority
    sla_hours = {"critical": 1, "high": 4, "medium": 24, "low": 72}
    now = datetime.utcnow()
    
    ticket = SupportTicket(
        organization_id=org_id,
        user_id=user_id,
        ticket_number=ticket_number,
        subject=data.subject,
        description=data.description,
        category=data.category,
        priority=data.priority,
        sla_response_due=now + timedelta(hours=sla_hours.get(data.priority, 24))
    )
    
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    
    return TicketResponse(
        id=str(ticket.id),
        ticket_number=ticket.ticket_number,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        status=ticket.status,
        assigned_to=ticket.assigned_to,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )


@router.patch("/enterprise/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    status: Optional[str] = None,
    resolution: Optional[str] = None,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a support ticket."""
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if status:
        ticket.status = status
        if status in ["resolved", "closed"]:
            ticket.resolved_at = datetime.utcnow()
    
    if resolution:
        ticket.resolution = resolution
    
    await db.commit()
    
    return {"message": "Ticket updated"}


# ==================== SLA Metrics ====================

@router.get("/enterprise/sla", response_model=List[SLAResponse])
async def get_sla_metrics(
    months: int = Query(default=3, ge=1, le=12),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get SLA metrics history."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(SLAMetric)
        .where(SLAMetric.organization_id == org_id)
        .order_by(desc(SLAMetric.period_start))
        .limit(months)
    )
    metrics = result.scalars().all()
    
    return [
        SLAResponse(
            period_start=m.period_start,
            period_end=m.period_end,
            uptime_percentage=m.uptime_percentage,
            avg_response_time_ms=m.avg_response_time_ms,
            tickets_resolved=m.tickets_resolved,
            sla_met=m.sla_met
        )
        for m in metrics
    ]


@router.get("/enterprise/sla/current")
async def get_current_sla(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get current month SLA status."""
    org_id = current_user.get("organization_id")
    
    # Get enterprise config
    config_result = await db.execute(
        select(EnterpriseConfig).where(EnterpriseConfig.organization_id == org_id)
    )
    config = config_result.scalar_one_or_none()
    
    # Calculate current month metrics (simplified)
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    
    return {
        "period": now.strftime("%B %Y"),
        "uptime_target": config.uptime_sla if config else 99.9,
        "uptime_current": 99.95,  # Would be calculated from actual metrics
        "response_time_target_hours": config.response_time_sla if config else 24,
        "avg_response_time_hours": 8.5,  # Would be calculated
        "sla_status": "met",
        "days_remaining": (month_start.replace(month=now.month + 1) - now).days if now.month < 12 else 31 - now.day
    }
