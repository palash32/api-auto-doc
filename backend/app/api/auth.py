"""Authentication endpoints: Email/Password and GitHub OAuth."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field, field_validator
import httpx
import uuid
import re

from app.core.config import settings
from app.core.database import get_async_db
from app.core.security import create_access_token, verify_token, get_password_hash, verify_password
from app.core.encryption import encrypt_token
from app.models.user import User, Organization, UserRole, SubscriptionTier
from app.core.logger import logger


# ============ Pydantic Schemas for Email/Password Auth ============

class RegisterRequest(BaseModel):
    """Registration request with production-ready validation."""
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (8-128 chars)")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Ensure password meets security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        """Sanitize and validate full name."""
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    """Authentication response with token."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        """Ensure new password meets security requirements."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


# ============ Email/Password Authentication Endpoints ============

@router.post("/register", response_model=AuthResponse)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Register a new user with email and password.
    
    Validates:
    - Email format and uniqueness
    - Password strength (8+ chars, uppercase, lowercase, digit)
    - Name length (2-100 chars)
    
    Returns:
        JWT access token and user info
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )
    
    # Create organization for new user
    org_subdomain = data.email.split('@')[0].lower().replace('.', '-').replace('_', '-')[:50]
    # Ensure unique subdomain by appending uuid if needed
    subdomain_check = await db.execute(
        select(Organization).where(Organization.subdomain == org_subdomain)
    )
    if subdomain_check.scalar_one_or_none():
        org_subdomain = f"{org_subdomain}-{str(uuid.uuid4())[:8]}"
    
    organization = Organization(
        name=f"{data.full_name}'s Workspace",
        subdomain=org_subdomain,
        subscription_tier=SubscriptionTier.FREE,
        developer_count=1
    )
    db.add(organization)
    await db.flush()
    
    # Create user with hashed password
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        organization_id=organization.id,
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=False  # Email verification can be added later
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"New user registered: {data.email}")
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return AuthResponse(
        access_token=access_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": str(user.organization_id),
            "role": user.role.value
        }
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Login with email and password.
    
    Returns:
        JWT access token and user info
        
    Raises:
        401: Invalid email or password
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    # Check if user exists and password is correct
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    logger.info(f"User logged in: {data.email}")
    
    # Update last login
    user.last_login = None  # Will trigger default timestamp
    await db.commit()
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return AuthResponse(
        access_token=access_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": str(user.organization_id),
            "role": user.role.value,
            "github_connected": user.github_id is not None
        }
    )


# ============ GitHub OAuth Endpoints ============

@router.get("/github/login")
async def github_login():
    """
    Initiate GitHub OAuth login flow.
    """
    logger.debug(f"GITHUB_CLIENT_ID = {settings.GITHUB_CLIENT_ID}")
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID in environment variables."
        )
    
    # Scopes: read user profile and access repos
    scope = "read:user repo"
    redirect_uri = settings.GITHUB_REDIRECT_URI
    
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
    )
    
    
    return RedirectResponse(url=github_auth_url)


@router.get("/google/login")
async def google_login():
    """
    Initiate Google OAuth login flow.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID in environment variables."
        )
    
    # Scopes: openid, email, profile
    scope = "openid email profile"
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    
    return {"client_id": settings.GOOGLE_CLIENT_ID, "redirect_url": google_auth_url}


@router.get("/github/callback")
async def github_callback(
    code: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Handle GitHub OAuth callback and create/login user.
    
    Args:
        code: Authorization code from GitHub
        db: Database session
        
    Returns:
        Redirects to frontend with JWT token
        
    Test:
        GET /auth/github/callback?code=GITHUB_CODE
        → Returns JWT token
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code"
        )
    
    # Step 1: Exchange code for GitHub access token
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
                headers={"Accept": "application/json"},
                timeout=10.0
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            
            if "error" in token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"GitHub error: {token_data.get('error_description', 'Unknown')}"
                )
            
            github_token = token_data.get("access_token")
            if not github_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token received from GitHub"
                )
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub communication error: {str(e)}"
        )
    
    # Step 2: Fetch user info from GitHub
    try:
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/json"
                },
                timeout=10.0
            )
            user_response.raise_for_status()
            github_user = user_response.json()
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch user from GitHub: {str(e)}"
        )
    
    # Step 3: Create or get existing user using GitHub ID (most reliable identifier)
    github_id = str(github_user["id"])  # GitHub numeric user ID - never changes
    github_username = github_user["login"]
    email = github_user.get("email") or f"{github_username}@users.noreply.github.com"
    full_name = github_user.get("name") or github_username
    
    # Primary lookup: by GitHub ID (most reliable)
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()
    
    # Fallback: by email (for users created before github_id was added)
    if not user:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            # Migrate existing user: add github_id for future logins
            user.github_id = github_id
            user.github_username = github_username
            logger.info(f"Migrated user {email} to use github_id {github_id}")
    
    if not user:
        # Create organization (MVP: one org per user)
        organization = Organization(
            name=f"{github_username}'s Workspace",
            subdomain=github_username.lower().replace("_", "-"),
            subscription_tier=SubscriptionTier.FREE,
            developer_count=1
        )
        db.add(organization)
        await db.flush()  # Get org ID
        
        # Create user with GitHub ID for reliable future lookups
        user = User(
            email=email,
            hashed_password="",  # OAuth users don't need password
            full_name=full_name,
            organization_id=organization.id,
            role=UserRole.ADMIN,  # First user is admin
            is_active=True,
            is_verified=True,
            github_id=github_id,
            github_username=github_username
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"Created new user: {email} with github_id {github_id}")
    else:
        # Update last login and ensure github info is current
        user.last_login = None  # Will be set by default
        user.github_username = github_username  # Username can change, so update it
        if not user.github_id:
            user.github_id = github_id
        await db.commit()
    
    # Step 4: Create JWT token for our app
    jwt_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    # Step 5: Redirect to frontend with token
    frontend_url = f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}"
    return RedirectResponse(url=frontend_url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Handle Google OAuth callback and create/login user.
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code"
        )
    
    # Step 1: Exchange code for Google access token
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                },
                headers={"Accept": "application/json"},
                timeout=10.0
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            
            google_token = token_data.get("access_token")
            id_token = token_data.get("id_token") # Google provides ID token
            
            if not google_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No access token received from Google"
                )
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Google communication error: {str(e)}"
        )
    
    # Step 2: Fetch user info from Google
    try:
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={
                    "Authorization": f"Bearer {google_token}",
                    "Accept": "application/json"
                },
                timeout=10.0
            )
            user_response.raise_for_status()
            google_user = user_response.json()
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch user from Google: {str(e)}"
        )
    
    # Step 3: Create or get existing user
    email = google_user.get("email")
    if not email:
         raise HTTPException(status_code=400, detail="Google account must have an email")
         
    full_name = google_user.get("name") or email.split("@")[0]
    
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create organization (MVP: one org per user)
        # Use email domain or name for org
        org_name = f"{full_name}'s Workspace"
        subdomain = str(uuid.uuid4())[:8] # Random subdomain for now to avoid conflicts
        
        organization = Organization(
            name=org_name,
            subdomain=subdomain,
            subscription_tier=SubscriptionTier.FREE,
            developer_count=1
        )
        db.add(organization)
        await db.flush()  # Get org ID
        
        # Create user
        user = User(
            email=email,
            hashed_password="",  # OAuth users don't need password
            full_name=full_name,
            organization_id=organization.id,
            role=UserRole.ADMIN,  # First user is admin
            is_active=True,
            is_verified=True # Google emails are verified
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update last login
        user.last_login = None  # Will be set by default
        await db.commit()
    
    # Step 4: Create JWT token for our app
    jwt_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    # Step 5: Redirect to frontend with token
    frontend_url = f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}"
    return RedirectResponse(url=frontend_url)


# Dependency for protected routes
async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Dependency to get current authenticated user.
    Returns user dict for use in protected endpoints.
    """
    # Verify JWT token
    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Fetch user from database
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )
        
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return {
        "sub": str(user.id),
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "organization_id": str(user.organization_id),
        "is_verified": user.is_verified
    }


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get current authenticated user.
    
    Headers:
        Authorization: Bearer {jwt_token}
        
    Returns:
        User information
        
    Test:
        GET /auth/me
        Authorization: Bearer eyJ...
        → Returns user data
    """
    # Verify JWT token
    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Fetch user from database
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )
        
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "organization_id": str(user.organization_id),
        "is_verified": user.is_verified
    }
