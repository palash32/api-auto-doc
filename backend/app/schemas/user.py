from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole, SubscriptionTier

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    subdomain: str = Field(..., min_length=2, max_length=100, pattern="^[a-z0-9-]+$")

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    subscription_tier: Optional[SubscriptionTier] = None

class OrganizationResponse(OrganizationBase):
    id: UUID
    subscription_tier: SubscriptionTier
    developer_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.DEVELOPER

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    organization_name: str = Field(..., min_length=2)
    subdomain: str = Field(..., min_length=2, pattern="^[a-z0-9-]+$")

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: UUID
    organization_id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    expires_at: Optional[datetime] = None

class APIKeyCreate(APIKeyBase):
    pass

class APIKeyResponse(APIKeyBase):
    id: UUID
    key_prefix: str
    is_active: bool
    last_used: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
