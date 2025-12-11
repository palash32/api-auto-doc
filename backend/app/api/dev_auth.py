"""Development-only authentication bypass."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.config import settings
from app.core.database import get_async_db
from app.core.security import verify_token
from app.models.user import User, Organization, UserRole, SubscriptionTier

security_optional = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    db: AsyncSession = Depends(get_async_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional)
) -> dict:
    """
    Optional authentication dependency for development.
    If no token is provided in development mode, creates/uses a test user.
    In production, requires authentication.
    """
    # If token is provided, validate it normally
    if credentials:
        try:
            token_data = verify_token(credentials.credentials)
            if token_data:
                user_id = token_data.get("sub")
                if user_id:
                    try:
                        user_uuid = uuid.UUID(user_id)
                        result = await db.execute(select(User).where(User.id == user_uuid))
                        user = result.scalar_one_or_none()
                        if user and user.is_active:
                            return {
                                "sub": str(user.id),
                                "id": str(user.id),
                                "email": user.email,
                                "full_name": user.full_name,
                                "role": user.role,
                                "organization_id": str(user.organization_id),
                                "is_verified": user.is_verified
                            }
                    except ValueError:
                        pass
        except:
            pass
    
    # Development mode: Create/get test user if no valid token
    if settings.is_development:
        # First, check if there's an existing user we can use
        test_email = "dev@test.com"
        result = await db.execute(select(User).where(User.email == test_email))
        user = result.scalar_one_or_none()
        
        if not user:
            # Try to find any existing organization (prefer ones with repos)
            result = await db.execute(
                select(Organization).order_by(Organization.created_at)
            )
            org = result.scalars().first()
            
            if not org:
                # Create test organization only if no orgs exist
                org = Organization(
                    name="Development Organization",
                    subdomain="dev-org",
                    subscription_tier=SubscriptionTier.FREE,
                    developer_count=1
                )
                db.add(org)
                await db.flush()
            
            # Create test user
            user = User(
                email=test_email,
                hashed_password="",
                full_name="Development User",
                organization_id=org.id,
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return {
            "sub": str(user.id),
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization_id": str(user.organization_id),
            "is_verified": user.is_verified
        }
    
    # Production: require authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
