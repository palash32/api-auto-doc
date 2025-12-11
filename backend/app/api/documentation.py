from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.api_endpoint import APIEndpoint
from app.core.database import get_async_session
from app.services.ai import ai_service
from uuid import UUID

router = APIRouter()

@router.post("/generate/{endpoint_id}")
async def generate_docs(
    endpoint_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Generate documentation for a specific endpoint using AI."""
    result = await session.execute(
        select(APIEndpoint).where(APIEndpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
        
    # In a real app, we would fetch the actual code snippet from the file
    # For MVP, we'll pass a placeholder or the summary as context
    code_context = f"def {endpoint.path.replace('/', '_')}():\n    '''{endpoint.summary}'''\n    pass"
    
    docs = await ai_service.generate_documentation(endpoint, code_context)
    
    if "error" in docs:
        raise HTTPException(status_code=500, detail=docs["error"])
        
    # Update endpoint with generated docs
    endpoint.summary = docs.get("summary", endpoint.summary)
    endpoint.description = docs.get("description", endpoint.description)
    endpoint.parameters = docs.get("parameters", [])
    endpoint.responses = docs.get("responses", {})
    endpoint.status = "healthy"
    
    await session.commit()
    await session.refresh(endpoint)
    
    return endpoint

@router.get("/{endpoint_id}")
async def get_docs(
    endpoint_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get documentation for a specific endpoint."""
    result = await session.execute(
        select(APIEndpoint).where(APIEndpoint.id == endpoint_id)
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return endpoint
