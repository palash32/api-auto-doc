"""Billing and monetization models for subscriptions and payments."""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
import enum

from app.core.database import Base


class PlanTier(enum.Enum):
    """Subscription plan tiers."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingInterval(enum.Enum):
    """Billing intervals."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class PaymentStatus(enum.Enum):
    """Payment status."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class SubscriptionPlan(Base):
    """
    Available subscription plans.
    """
    __tablename__ = "subscription_plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Plan details
    name = Column(String(100), nullable=False)
    tier = Column(String(20), nullable=False)  # free, starter, pro, enterprise
    description = Column(Text, nullable=True)
    
    # Pricing
    price_monthly = Column(Float, default=0)
    price_yearly = Column(Float, default=0)
    currency = Column(String(3), default="USD")
    
    # Stripe IDs
    stripe_price_monthly_id = Column(String(100), nullable=True)
    stripe_price_yearly_id = Column(String(100), nullable=True)
    stripe_product_id = Column(String(100), nullable=True)
    
    # Limits
    max_repositories = Column(Integer, default=1)
    max_endpoints = Column(Integer, default=100)
    max_team_members = Column(Integer, default=1)
    max_api_calls_per_month = Column(Integer, default=1000)
    
    # Features
    features = Column(JSON, nullable=True)  # ["AI Analysis", "Custom Branding", etc.]
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    """
    Organization subscription.
    """
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(String(36), ForeignKey("subscription_plans.id"), nullable=False)
    
    # Stripe subscription
    stripe_subscription_id = Column(String(100), nullable=True)
    stripe_customer_id = Column(String(100), nullable=True)
    
    # Billing
    billing_interval = Column(String(20), default="monthly")  # monthly, yearly
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(20), default="active")  # active, canceled, past_due, trialing
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)
    
    # Trial
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="subscription", uselist=False)
    plan = relationship("SubscriptionPlan", backref="subscriptions")


class UsageRecord(Base):
    """
    Track usage for usage-based billing.
    """
    __tablename__ = "usage_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    
    # Usage details
    metric_name = Column(String(50), nullable=False)  # api_calls, ai_enhancements, repos, etc.
    quantity = Column(Integer, default=1)
    
    # Billing period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Stripe
    stripe_usage_record_id = Column(String(100), nullable=True)
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow)


class Invoice(Base):
    """
    Invoice record.
    """
    __tablename__ = "invoices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    
    # Invoice details
    invoice_number = Column(String(50), nullable=False)
    
    # Stripe
    stripe_invoice_id = Column(String(100), nullable=True)
    stripe_hosted_url = Column(String(500), nullable=True)
    stripe_pdf_url = Column(String(500), nullable=True)
    
    # Amounts
    subtotal = Column(Float, default=0)
    tax = Column(Float, default=0)
    total = Column(Float, default=0)
    amount_paid = Column(Float, default=0)
    amount_due = Column(Float, default=0)
    currency = Column(String(3), default="USD")
    
    # Line items
    line_items = Column(JSON, nullable=True)  # [{description, quantity, amount}]
    
    # Status
    status = Column(String(20), default="draft")  # draft, open, paid, void, uncollectible
    
    # Dates
    invoice_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="invoices")


class PaymentMethod(Base):
    """
    Stored payment methods.
    """
    __tablename__ = "payment_methods"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Stripe
    stripe_payment_method_id = Column(String(100), nullable=False)
    
    # Card details (masked)
    card_brand = Column(String(20), nullable=True)  # visa, mastercard, amex
    card_last4 = Column(String(4), nullable=True)
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)
    
    # Status
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="payment_methods")


class PaymentHistory(Base):
    """
    Payment transaction history.
    """
    __tablename__ = "payment_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    
    # Payment details
    stripe_payment_intent_id = Column(String(100), nullable=True)
    stripe_charge_id = Column(String(100), nullable=True)
    
    # Amount
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Status
    status = Column(String(20), default="pending")  # pending, succeeded, failed, refunded
    failure_reason = Column(Text, nullable=True)
    
    # Metadata
    description = Column(String(200), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", backref="payment_history")
