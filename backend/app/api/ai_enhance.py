"""AI Enhancement API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.services.advanced_ai_service import advanced_ai_service
from app.models.api_endpoint import APIEndpoint
from app.models.repository import Repository

router = APIRouter()


# ==================== Pydantic Schemas ====================

class EnhanceDescriptionRequest(BaseModel):
    description: str
    endpoint_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class EnhanceDescriptionResponse(BaseModel):
    original: str
    enhanced: str
    summary: str
    improvements: List[str]


class GenerateExamplesRequest(BaseModel):
    endpoint_id: Optional[str] = None
    method: str = "GET"
    path: str = "/"
    parameters: Optional[List[dict]] = None
    request_body: Optional[dict] = None
    languages: Optional[List[str]] = None


class GeneratedExampleResponse(BaseModel):
    language: str
    code: str
    description: str


class InferTypesRequest(BaseModel):
    code: str
    language: str = "python"


class TypeInferenceResponse(BaseModel):
    param_name: str
    inferred_type: str
    confidence: float
    reason: str


class BreakingChangeResponse(BaseModel):
    change_type: str
    path: str
    field: Optional[str]
    old_value: Any
    new_value: Any
    severity: str
    description: str


class QualityScoreResponse(BaseModel):
    overall_score: int
    categories: Dict[str, int]
    issues: List[str]
    suggestions: List[str]


# ==================== Endpoints ====================

@router.post("/enhance-description", response_model=EnhanceDescriptionResponse)
async def enhance_description(
    data: EnhanceDescriptionRequest,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Enhance an API endpoint description using AI.
    
    Takes a brief or unclear description and returns an improved version
    with better clarity, completeness, and technical accuracy.
    """
    context = data.context or {}
    
    # Get endpoint context if ID provided
    if data.endpoint_id:
        result = await db.execute(
            select(APIEndpoint).where(APIEndpoint.id == data.endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        if endpoint:
            context = {
                "method": endpoint.method,
                "path": endpoint.path,
                "parameters": endpoint.parameters or [],
                "request_body": endpoint.request_body
            }
    
    result = await advanced_ai_service.enhance_description(
        original_description=data.description,
        endpoint_context=context
    )
    
    return EnhanceDescriptionResponse(
        original=result.original,
        enhanced=result.enhanced,
        summary=result.summary,
        improvements=result.improvements
    )


@router.post("/generate-examples", response_model=List[GeneratedExampleResponse])
async def generate_examples(
    data: GenerateExamplesRequest,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Generate code examples for an API endpoint in multiple languages.
    
    Returns ready-to-use code snippets for cURL, Python, JavaScript, etc.
    """
    endpoint_data = {
        "method": data.method,
        "path": data.path,
        "parameters": data.parameters or [],
        "request_body": data.request_body
    }
    
    # Get endpoint details if ID provided
    if data.endpoint_id:
        result = await db.execute(
            select(APIEndpoint).where(APIEndpoint.id == data.endpoint_id)
        )
        endpoint = result.scalar_one_or_none()
        if endpoint:
            endpoint_data = {
                "method": endpoint.method,
                "path": endpoint.path,
                "description": endpoint.description,
                "parameters": endpoint.parameters or [],
                "request_body": endpoint.request_body
            }
    
    examples = await advanced_ai_service.generate_examples(
        endpoint=endpoint_data,
        languages=data.languages
    )
    
    return [
        GeneratedExampleResponse(
            language=ex.language,
            code=ex.code,
            description=ex.description
        )
        for ex in examples
    ]


@router.post("/infer-types", response_model=List[TypeInferenceResponse])
async def infer_types(
    data: InferTypesRequest,
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Infer parameter types from source code using AI analysis.
    
    Analyzes code to determine parameter and return types with confidence scores.
    """
    inferences = await advanced_ai_service.infer_types(
        code_snippet=data.code,
        language=data.language
    )
    
    return [
        TypeInferenceResponse(
            param_name=inf.param_name,
            inferred_type=inf.inferred_type,
            confidence=inf.confidence,
            reason=inf.reason
        )
        for inf in inferences
    ]


@router.post("/detect-breaking-changes", response_model=List[BreakingChangeResponse])
async def detect_breaking_changes(
    old_spec: Dict[str, Any],
    new_spec: Dict[str, Any],
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Detect breaking changes between two API versions.
    
    Compares two API specifications and identifies potentially breaking changes
    like removed endpoints, changed parameters, or type modifications.
    """
    changes = await advanced_ai_service.detect_breaking_changes(
        old_spec=old_spec,
        new_spec=new_spec
    )
    
    return [
        BreakingChangeResponse(
            change_type=c.change_type,
            path=c.path,
            field=c.field,
            old_value=c.old_value,
            new_value=c.new_value,
            severity=c.severity,
            description=c.description
        )
        for c in changes
    ]


@router.get("/quality-score/{repository_id}", response_model=QualityScoreResponse)
async def get_quality_score(
    repository_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get API quality score for a repository.
    
    Analyzes endpoint naming, consistency, documentation coverage,
    and design patterns to provide a quality score with suggestions.
    """
    # Get endpoints for repository
    result = await db.execute(
        select(APIEndpoint).where(APIEndpoint.repository_id == repository_id)
    )
    endpoints = result.scalars().all()
    
    if not endpoints:
        raise HTTPException(status_code=404, detail="No endpoints found for repository")
    
    # Convert to dicts for scoring
    endpoint_data = [
        {
            "path": e.path,
            "method": e.method,
            "description": e.description,
            "parameters": e.parameters
        }
        for e in endpoints
    ]
    
    score = await advanced_ai_service.score_api_quality(endpoint_data)
    
    return QualityScoreResponse(
        overall_score=score.overall_score,
        categories=score.categories,
        issues=score.issues,
        suggestions=score.suggestions
    )


@router.post("/bulk-enhance/{repository_id}")
async def bulk_enhance_descriptions(
    repository_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Enhance all endpoint descriptions in a repository.
    
    Processes each endpoint with missing or brief descriptions
    and updates them with AI-enhanced versions.
    """
    # Get endpoints
    result = await db.execute(
        select(APIEndpoint).where(
            APIEndpoint.repository_id == repository_id
        )
    )
    endpoints = result.scalars().all()
    
    enhanced_count = 0
    skipped_count = 0
    
    for endpoint in endpoints:
        # Skip if already has good description
        if endpoint.description and len(endpoint.description) > 50:
            skipped_count += 1
            continue
        
        context = {
            "method": endpoint.method,
            "path": endpoint.path,
            "parameters": endpoint.parameters or []
        }
        
        enhanced = await advanced_ai_service.enhance_description(
            original_description=endpoint.description or "",
            endpoint_context=context
        )
        
        if enhanced.enhanced and enhanced.enhanced != endpoint.description:
            endpoint.description = enhanced.enhanced
            endpoint.summary = enhanced.summary
            enhanced_count += 1
    
    await db.commit()
    
    return {
        "message": f"Enhanced {enhanced_count} descriptions, skipped {skipped_count}",
        "enhanced": enhanced_count,
        "skipped": skipped_count,
        "total": len(endpoints)
    }
