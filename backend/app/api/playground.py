"""API endpoints for the API Playground feature."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
import httpx

from app.core.database import get_async_db
from app.core.encryption import encrypt_token, decrypt_token
from app.api.dev_auth import get_current_user_optional
from app.models.playground import PlaygroundToken, PlaygroundEnvironment, PlaygroundRequest

router = APIRouter()


# ==================== Pydantic Schemas ====================

class TokenCreate(BaseModel):
    name: str
    token_type: str = "bearer"  # bearer, api_key, basic
    value: str
    description: Optional[str] = None
    expires_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    id: str
    name: str
    token_type: str
    prefix: Optional[str]
    description: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class EnvironmentCreate(BaseModel):
    name: str
    variables: dict = {}
    is_default: bool = False


class EnvironmentResponse(BaseModel):
    id: str
    name: str
    variables: dict
    is_default: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProxyRequest(BaseModel):
    method: str
    url: str
    headers: dict = {}
    body: Optional[str] = None
    token_id: Optional[str] = None  # Use saved token


class RequestHistoryResponse(BaseModel):
    id: str
    method: str
    url: str
    response_status: Optional[str]
    response_time_ms: Optional[str]
    name: Optional[str]
    is_saved: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Token Vault Endpoints ====================

@router.post("/tokens", response_model=TokenResponse)
async def create_token(
    token_data: TokenCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Store a new API token securely."""
    user_id = UUID(current_user["id"])
    
    # Encrypt the token value
    encrypted = encrypt_token(token_data.value)
    
    # Create prefix for display (e.g., "sk-...xxxx")
    prefix = None
    if len(token_data.value) > 8:
        prefix = f"{token_data.value[:4]}...{token_data.value[-4:]}"
    
    token = PlaygroundToken(
        user_id=user_id,
        name=token_data.name,
        token_type=token_data.token_type,
        encrypted_value=encrypted,
        prefix=prefix,
        description=token_data.description,
        expires_at=token_data.expires_at
    )
    
    db.add(token)
    await db.commit()
    await db.refresh(token)
    
    return TokenResponse(
        id=str(token.id),
        name=token.name,
        token_type=token.token_type,
        prefix=token.prefix,
        description=token.description,
        expires_at=token.expires_at,
        created_at=token.created_at,
        last_used_at=token.last_used_at
    )


@router.get("/tokens", response_model=List[TokenResponse])
async def list_tokens(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List all saved tokens for the user."""
    user_id = UUID(current_user["id"])
    
    result = await db.execute(
        select(PlaygroundToken).where(PlaygroundToken.user_id == user_id)
    )
    tokens = result.scalars().all()
    
    return [
        TokenResponse(
            id=str(t.id),
            name=t.name,
            token_type=t.token_type,
            prefix=t.prefix,
            description=t.description,
            expires_at=t.expires_at,
            created_at=t.created_at,
            last_used_at=t.last_used_at
        )
        for t in tokens
    ]


@router.delete("/tokens/{token_id}")
async def delete_token(
    token_id: UUID,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a saved token."""
    user_id = UUID(current_user["id"])
    
    result = await db.execute(
        select(PlaygroundToken).where(
            PlaygroundToken.id == token_id,
            PlaygroundToken.user_id == user_id
        )
    )
    token = result.scalar_one_or_none()
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    await db.delete(token)
    await db.commit()
    
    return {"message": "Token deleted"}


# ==================== Environment Endpoints ====================

@router.post("/environments", response_model=EnvironmentResponse)
async def create_environment(
    env_data: EnvironmentCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new environment."""
    user_id = UUID(current_user["id"])
    
    # If this is set as default, unset other defaults
    if env_data.is_default:
        await db.execute(
            select(PlaygroundEnvironment)
            .where(PlaygroundEnvironment.user_id == user_id, PlaygroundEnvironment.is_default == True)
        )
        # Update existing defaults - simplified for now
    
    env = PlaygroundEnvironment(
        user_id=user_id,
        name=env_data.name,
        variables=env_data.variables,
        is_default=env_data.is_default
    )
    
    db.add(env)
    await db.commit()
    await db.refresh(env)
    
    return EnvironmentResponse(
        id=str(env.id),
        name=env.name,
        variables=env.variables,
        is_default=env.is_default,
        created_at=env.created_at
    )


@router.get("/environments", response_model=List[EnvironmentResponse])
async def list_environments(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List all environments for the user."""
    user_id = UUID(current_user["id"])
    
    result = await db.execute(
        select(PlaygroundEnvironment).where(PlaygroundEnvironment.user_id == user_id)
    )
    envs = result.scalars().all()
    
    return [
        EnvironmentResponse(
            id=str(e.id),
            name=e.name,
            variables=e.variables,
            is_default=e.is_default,
            created_at=e.created_at
        )
        for e in envs
    ]


# ==================== API Proxy Endpoint ====================

@router.post("/proxy")
async def proxy_request(
    request: ProxyRequest,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Proxy an API request to avoid CORS issues.
    Optionally uses a saved token for authentication.
    """
    user_id = UUID(current_user["id"])
    headers = dict(request.headers)
    
    # If token_id provided, fetch and inject the token
    if request.token_id:
        result = await db.execute(
            select(PlaygroundToken).where(
                PlaygroundToken.id == UUID(request.token_id),
                PlaygroundToken.user_id == user_id
            )
        )
        token = result.scalar_one_or_none()
        
        if token:
            decrypted = decrypt_token(token.encrypted_value)
            
            if token.token_type == "bearer":
                headers["Authorization"] = f"Bearer {decrypted}"
            elif token.token_type == "api_key":
                headers["X-API-Key"] = decrypted
            elif token.token_type == "basic":
                import base64
                headers["Authorization"] = f"Basic {base64.b64encode(decrypted.encode()).decode()}"
            
            # Update last_used
            token.last_used_at = datetime.utcnow()
            token.use_count = str(int(token.use_count or "0") + 1)
            await db.commit()
    
    # Make the actual request
    start_time = datetime.utcnow()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method.upper(),
                url=request.url,
                headers=headers,
                content=request.body if request.body else None
            )
        
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Save to history
        history_entry = PlaygroundRequest(
            user_id=user_id,
            method=request.method.upper(),
            url=request.url,
            headers=request.headers,
            body=request.body,
            response_status=str(response.status_code),
            response_time_ms=str(duration_ms)
        )
        db.add(history_entry)
        await db.commit()
        
        # Return response
        return {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "time_ms": duration_ms
        }
        
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Request failed: {str(e)}"
        )


# ==================== Request History Endpoints ====================

@router.get("/history", response_model=List[RequestHistoryResponse])
async def get_request_history(
    limit: int = 50,
    saved_only: bool = False,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get request history for the user."""
    user_id = UUID(current_user["id"])
    
    query = select(PlaygroundRequest).where(PlaygroundRequest.user_id == user_id)
    
    if saved_only:
        query = query.where(PlaygroundRequest.is_saved == True)
    
    query = query.order_by(PlaygroundRequest.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return [
        RequestHistoryResponse(
            id=str(r.id),
            method=r.method,
            url=r.url,
            response_status=r.response_status,
            response_time_ms=r.response_time_ms,
            name=r.name,
            is_saved=r.is_saved,
            created_at=r.created_at
        )
        for r in requests
    ]


@router.post("/history/{request_id}/save")
async def save_request(
    request_id: UUID,
    name: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Save/favorite a request from history."""
    user_id = UUID(current_user["id"])
    
    result = await db.execute(
        select(PlaygroundRequest).where(
            PlaygroundRequest.id == request_id,
            PlaygroundRequest.user_id == user_id
        )
    )
    req = result.scalar_one_or_none()
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    req.is_saved = True
    req.name = name
    await db.commit()
    
    return {"message": "Request saved"}


@router.delete("/history")
async def clear_history(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Clear unsaved request history."""
    user_id = UUID(current_user["id"])
    
    await db.execute(
        delete(PlaygroundRequest).where(
            PlaygroundRequest.user_id == user_id,
            PlaygroundRequest.is_saved == False
        )
    )
    await db.commit()
    
    return {"message": "History cleared"}
