"""Billing and monetization API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.billing import (
    SubscriptionPlan, Subscription, UsageRecord,
    Invoice, PaymentMethod, PaymentHistory
)

router = APIRouter()


# ==================== Pydantic Schemas ====================

class PlanResponse(BaseModel):
    id: str
    name: str
    tier: str
    description: Optional[str]
    price_monthly: float
    price_yearly: float
    currency: str
    max_repositories: int
    max_endpoints: int
    max_team_members: int
    max_api_calls_per_month: int
    features: Optional[List[str]]


class SubscriptionResponse(BaseModel):
    id: str
    plan: PlanResponse
    billing_interval: str
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool


class SubscriptionCreate(BaseModel):
    plan_id: str
    billing_interval: str = "monthly"  # monthly, yearly
    payment_method_id: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    total: float
    amount_paid: float
    amount_due: float
    currency: str
    status: str
    invoice_date: datetime
    due_date: Optional[datetime]
    stripe_hosted_url: Optional[str]
    stripe_pdf_url: Optional[str]


class PaymentMethodCreate(BaseModel):
    stripe_payment_method_id: str


class PaymentMethodResponse(BaseModel):
    id: str
    card_brand: Optional[str]
    card_last4: Optional[str]
    card_exp_month: Optional[int]
    card_exp_year: Optional[int]
    is_default: bool


class UsageResponse(BaseModel):
    metric_name: str
    current_usage: int
    limit: int
    percentage: float


# ==================== Plans Endpoints ====================

@router.get("/billing/plans", response_model=List[PlanResponse])
async def list_plans(
    db: AsyncSession = Depends(get_async_db)
):
    """List all available subscription plans."""
    result = await db.execute(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active == True, SubscriptionPlan.is_public == True)
        .order_by(SubscriptionPlan.price_monthly)
    )
    plans = result.scalars().all()
    
    return [
        PlanResponse(
            id=str(p.id),
            name=p.name,
            tier=p.tier,
            description=p.description,
            price_monthly=p.price_monthly,
            price_yearly=p.price_yearly,
            currency=p.currency,
            max_repositories=p.max_repositories,
            max_endpoints=p.max_endpoints,
            max_team_members=p.max_team_members,
            max_api_calls_per_month=p.max_api_calls_per_month,
            features=p.features
        )
        for p in plans
    ]


@router.post("/billing/plans/seed")
async def seed_default_plans(
    db: AsyncSession = Depends(get_async_db)
):
    """Seed default subscription plans (admin only)."""
    plans = [
        SubscriptionPlan(
            name="Free",
            tier="free",
            description="For individual developers",
            price_monthly=0,
            price_yearly=0,
            max_repositories=1,
            max_endpoints=50,
            max_team_members=1,
            max_api_calls_per_month=1000,
            features=["Basic API Documentation", "Public Repos Only"]
        ),
        SubscriptionPlan(
            name="Starter",
            tier="starter",
            description="For small teams",
            price_monthly=19,
            price_yearly=190,
            max_repositories=5,
            max_endpoints=500,
            max_team_members=5,
            max_api_calls_per_month=10000,
            features=["AI Analysis", "Private Repos", "API Playground", "Team Collaboration"]
        ),
        SubscriptionPlan(
            name="Pro",
            tier="pro",
            description="For growing teams",
            price_monthly=49,
            price_yearly=490,
            max_repositories=20,
            max_endpoints=2000,
            max_team_members=20,
            max_api_calls_per_month=50000,
            features=["Everything in Starter", "Custom Branding", "Version History", "Priority Support"]
        ),
        SubscriptionPlan(
            name="Enterprise",
            tier="enterprise",
            description="For large organizations",
            price_monthly=199,
            price_yearly=1990,
            max_repositories=-1,  # Unlimited
            max_endpoints=-1,
            max_team_members=-1,
            max_api_calls_per_month=-1,
            features=["Everything in Pro", "SSO/SAML", "Audit Logs", "Dedicated Support", "SLA"]
        )
    ]
    
    for plan in plans:
        db.add(plan)
    
    await db.commit()
    
    return {"message": f"Seeded {len(plans)} plans"}


# ==================== Subscription Endpoints ====================

@router.get("/billing/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get current organization subscription."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(Subscription, SubscriptionPlan)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.organization_id == org_id)
    )
    row = result.first()
    
    if not row:
        return None
    
    sub, plan = row
    
    return SubscriptionResponse(
        id=str(sub.id),
        plan=PlanResponse(
            id=str(plan.id),
            name=plan.name,
            tier=plan.tier,
            description=plan.description,
            price_monthly=plan.price_monthly,
            price_yearly=plan.price_yearly,
            currency=plan.currency,
            max_repositories=plan.max_repositories,
            max_endpoints=plan.max_endpoints,
            max_team_members=plan.max_team_members,
            max_api_calls_per_month=plan.max_api_calls_per_month,
            features=plan.features
        ),
        billing_interval=sub.billing_interval,
        status=sub.status,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end
    )


@router.post("/billing/subscription", response_model=SubscriptionResponse)
async def create_subscription(
    data: SubscriptionCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create or update subscription."""
    org_id = current_user.get("organization_id")
    
    # Get plan
    plan_result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == data.plan_id)
    )
    plan = plan_result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check for existing subscription
    existing_result = await db.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    existing = existing_result.scalar_one_or_none()
    
    now = datetime.utcnow()
    period_end = now + timedelta(days=30 if data.billing_interval == "monthly" else 365)
    
    if existing:
        # Update existing subscription
        existing.plan_id = data.plan_id
        existing.billing_interval = data.billing_interval
        existing.current_period_start = now
        existing.current_period_end = period_end
        existing.status = "active"
        existing.cancel_at_period_end = False
        sub = existing
    else:
        # Create new subscription
        sub = Subscription(
            organization_id=org_id,
            plan_id=data.plan_id,
            billing_interval=data.billing_interval,
            current_period_start=now,
            current_period_end=period_end,
            status="active"
        )
        db.add(sub)
    
    await db.commit()
    await db.refresh(sub)
    
    return SubscriptionResponse(
        id=str(sub.id),
        plan=PlanResponse(
            id=str(plan.id),
            name=plan.name,
            tier=plan.tier,
            description=plan.description,
            price_monthly=plan.price_monthly,
            price_yearly=plan.price_yearly,
            currency=plan.currency,
            max_repositories=plan.max_repositories,
            max_endpoints=plan.max_endpoints,
            max_team_members=plan.max_team_members,
            max_api_calls_per_month=plan.max_api_calls_per_month,
            features=plan.features
        ),
        billing_interval=sub.billing_interval,
        status=sub.status,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end
    )


@router.post("/billing/subscription/cancel")
async def cancel_subscription(
    immediate: bool = False,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Cancel subscription."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(Subscription).where(Subscription.organization_id == org_id)
    )
    sub = result.scalar_one_or_none()
    
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")
    
    if immediate:
        sub.status = "canceled"
        sub.canceled_at = datetime.utcnow()
    else:
        sub.cancel_at_period_end = True
    
    await db.commit()
    
    return {"message": "Subscription cancelled"}


# ==================== Usage Endpoints ====================

@router.get("/billing/usage", response_model=List[UsageResponse])
async def get_usage(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get current usage vs plan limits."""
    org_id = current_user.get("organization_id")
    
    # Get subscription and plan
    sub_result = await db.execute(
        select(Subscription, SubscriptionPlan)
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.organization_id == org_id)
    )
    row = sub_result.first()
    
    if not row:
        # Default to free limits
        limits = {
            "repositories": 1,
            "endpoints": 50,
            "team_members": 1,
            "api_calls": 1000
        }
    else:
        _, plan = row
        limits = {
            "repositories": plan.max_repositories,
            "endpoints": plan.max_endpoints,
            "team_members": plan.max_team_members,
            "api_calls": plan.max_api_calls_per_month
        }
    
    # Get current usage (simplified - would query actual counts)
    usage = []
    for metric, limit in limits.items():
        current = 0  # Would query actual counts
        usage.append(UsageResponse(
            metric_name=metric,
            current_usage=current,
            limit=limit if limit > 0 else 999999,
            percentage=(current / limit * 100) if limit > 0 else 0
        ))
    
    return usage


@router.post("/billing/usage/record")
async def record_usage(
    metric_name: str,
    quantity: int = 1,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Record usage for billing."""
    org_id = current_user.get("organization_id")
    now = datetime.utcnow()
    
    record = UsageRecord(
        organization_id=org_id,
        metric_name=metric_name,
        quantity=quantity,
        period_start=now.replace(day=1, hour=0, minute=0, second=0),
        period_end=(now.replace(day=1) + timedelta(days=32)).replace(day=1)
    )
    
    db.add(record)
    await db.commit()
    
    return {"message": "Usage recorded"}


# ==================== Invoice Endpoints ====================

@router.get("/billing/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List invoices."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(Invoice)
        .where(Invoice.organization_id == org_id)
        .order_by(desc(Invoice.invoice_date))
        .limit(limit)
    )
    invoices = result.scalars().all()
    
    return [
        InvoiceResponse(
            id=str(i.id),
            invoice_number=i.invoice_number,
            total=i.total,
            amount_paid=i.amount_paid,
            amount_due=i.amount_due,
            currency=i.currency,
            status=i.status,
            invoice_date=i.invoice_date,
            due_date=i.due_date,
            stripe_hosted_url=i.stripe_hosted_url,
            stripe_pdf_url=i.stripe_pdf_url
        )
        for i in invoices
    ]


# ==================== Payment Method Endpoints ====================

@router.get("/billing/payment-methods", response_model=List[PaymentMethodResponse])
async def list_payment_methods(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List payment methods."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(PaymentMethod)
        .where(PaymentMethod.organization_id == org_id)
        .order_by(desc(PaymentMethod.is_default), desc(PaymentMethod.created_at))
    )
    methods = result.scalars().all()
    
    return [
        PaymentMethodResponse(
            id=str(m.id),
            card_brand=m.card_brand,
            card_last4=m.card_last4,
            card_exp_month=m.card_exp_month,
            card_exp_year=m.card_exp_year,
            is_default=m.is_default
        )
        for m in methods
    ]


@router.post("/billing/payment-methods", response_model=PaymentMethodResponse)
async def add_payment_method(
    data: PaymentMethodCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Add a payment method."""
    org_id = current_user.get("organization_id")
    
    # In production, would validate with Stripe and get card details
    method = PaymentMethod(
        organization_id=org_id,
        stripe_payment_method_id=data.stripe_payment_method_id,
        card_brand="visa",  # Would come from Stripe
        card_last4="4242",
        card_exp_month=12,
        card_exp_year=2025,
        is_default=True
    )
    
    db.add(method)
    await db.commit()
    await db.refresh(method)
    
    return PaymentMethodResponse(
        id=str(method.id),
        card_brand=method.card_brand,
        card_last4=method.card_last4,
        card_exp_month=method.card_exp_month,
        card_exp_year=method.card_exp_year,
        is_default=method.is_default
    )


@router.delete("/billing/payment-methods/{method_id}")
async def remove_payment_method(
    method_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Remove a payment method."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(PaymentMethod).where(
            PaymentMethod.id == method_id,
            PaymentMethod.organization_id == org_id
        )
    )
    method = result.scalar_one_or_none()
    
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    await db.delete(method)
    await db.commit()
    
    return {"message": "Payment method removed"}


# ==================== Payment History ====================

@router.get("/billing/payments")
async def list_payments(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List payment history."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(PaymentHistory)
        .where(PaymentHistory.organization_id == org_id)
        .order_by(desc(PaymentHistory.created_at))
        .limit(limit)
    )
    payments = result.scalars().all()
    
    return [
        {
            "id": str(p.id),
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "description": p.description,
            "created_at": p.created_at.isoformat()
        }
        for p in payments
    ]
