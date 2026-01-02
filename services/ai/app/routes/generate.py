"""
Documentation generation routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.services.gemini_service import generate_documentation, DocumentationResult
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class EndpointInput(BaseModel):
    """Input for documentation generation."""
    path: str
    method: str
    code_snippet: str
    file_path: Optional[str] = None
    language: Optional[str] = None


class GenerateRequest(BaseModel):
    """Request to generate documentation for an endpoint."""
    endpoint: EndpointInput


class BatchGenerateRequest(BaseModel):
    """Request to generate documentation for multiple endpoints."""
    endpoints: List[EndpointInput]


@router.post("")
async def generate(request: GenerateRequest):
    """
    Generate documentation for a single endpoint.
    
    Uses Google Gemini to analyze code and generate:
    - Summary
    - Description
    - Parameters
    - Request body schema
    - Response schema
    """
    if not settings.GEMINI_API_KEY:
        # Fallback to basic extraction
        return {
            "success": True,
            "fallback": True,
            "documentation": {
                "summary": f"{request.endpoint.method} {request.endpoint.path}",
                "description": "Documentation generated without AI (API key not configured)",
                "parameters": [],
                "request_body": None,
                "responses": [{"status": 200, "description": "Success"}]
            },
            "cost": 0.0
        }
    
    try:
        result = await generate_documentation(request.endpoint)
        return {
            "success": True,
            "fallback": False,
            "documentation": result.documentation,
            "cost": result.cost,
            "tokens": {
                "input": result.input_tokens,
                "output": result.output_tokens
            }
        }
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_generate(request: BatchGenerateRequest):
    """
    Generate documentation for multiple endpoints.
    """
    results = []
    total_cost = 0.0
    
    for endpoint in request.endpoints:
        try:
            if settings.GEMINI_API_KEY:
                result = await generate_documentation(endpoint)
                results.append({
                    "path": endpoint.path,
                    "method": endpoint.method,
                    "success": True,
                    "documentation": result.documentation,
                    "cost": result.cost
                })
                total_cost += result.cost
            else:
                results.append({
                    "path": endpoint.path,
                    "method": endpoint.method,
                    "success": True,
                    "fallback": True,
                    "documentation": {
                        "summary": f"{endpoint.method} {endpoint.path}",
                        "description": "No AI key configured"
                    }
                })
        except Exception as e:
            results.append({
                "path": endpoint.path,
                "method": endpoint.method,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total": len(results),
        "successful": sum(1 for r in results if r["success"]),
        "total_cost": round(total_cost, 4),
        "results": results
    }
