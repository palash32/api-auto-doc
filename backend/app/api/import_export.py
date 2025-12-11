"""Import/Export API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.import_export import ImportJob, ExportJob, ExportTemplate
from app.models.api_endpoint import APIEndpoint
from app.models.repository import Repository

router = APIRouter()


# ==================== Pydantic Schemas ====================

class ImportRequest(BaseModel):
    repository_id: str
    format: str  # openapi_3.0, swagger_2.0, postman_2.1
    source_url: Optional[str] = None
    content: Optional[str] = None  # JSON/YAML content directly


class ImportResponse(BaseModel):
    id: str
    status: str
    endpoints_imported: int
    endpoints_updated: int
    endpoints_skipped: int


class ExportRequest(BaseModel):
    repository_id: str
    format: str  # openapi_3.0, postman_2.1, markdown, pdf, html
    title: Optional[str] = None
    version: Optional[str] = "1.0.0"
    base_url: Optional[str] = None
    include_examples: bool = True


class ExportResponse(BaseModel):
    id: str
    format: str
    status: str
    output_url: Optional[str]


class JobResponse(BaseModel):
    id: str
    format: str
    status: str
    created_at: datetime


# ==================== Import Endpoints ====================

@router.post("/import", response_model=ImportResponse)
async def import_api_spec(
    data: ImportRequest,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Import API specification (OpenAPI, Swagger, Postman)."""
    # Create import job
    job = ImportJob(
        repository_id=data.repository_id,
        format=data.format,
        source_url=data.source_url,
        status="processing",
        started_at=datetime.utcnow()
    )
    db.add(job)
    
    try:
        # Parse the content
        if data.content:
            spec = json.loads(data.content)
        elif data.source_url:
            # Would fetch from URL
            spec = {}
        else:
            raise HTTPException(status_code=400, detail="No content or URL provided")
        
        # Process based on format
        imported = 0
        updated = 0
        skipped = 0
        
        if data.format.startswith("openapi") or data.format.startswith("swagger"):
            imported, updated, skipped = await _import_openapi(spec, data.repository_id, db)
        elif data.format.startswith("postman"):
            imported, updated, skipped = await _import_postman(spec, data.repository_id, db)
        
        job.status = "completed"
        job.endpoints_imported = imported
        job.endpoints_updated = updated
        job.endpoints_skipped = skipped
        job.completed_at = datetime.utcnow()
        
    except Exception as e:
        job.status = "failed"
        job.errors = [str(e)]
    
    await db.commit()
    await db.refresh(job)
    
    return ImportResponse(
        id=str(job.id),
        status=job.status,
        endpoints_imported=job.endpoints_imported,
        endpoints_updated=job.endpoints_updated,
        endpoints_skipped=job.endpoints_skipped
    )


@router.get("/import/jobs", response_model=List[JobResponse])
async def list_import_jobs(
    repository_id: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List import jobs."""
    query = select(ImportJob)
    
    if repository_id:
        query = query.where(ImportJob.repository_id == repository_id)
    
    query = query.order_by(desc(ImportJob.created_at)).limit(limit)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return [
        JobResponse(
            id=str(j.id),
            format=j.format,
            status=j.status,
            created_at=j.created_at
        )
        for j in jobs
    ]


# ==================== Export Endpoints ====================

@router.post("/export", response_model=ExportResponse)
async def export_api_docs(
    data: ExportRequest,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Export API documentation in various formats."""
    # Get repository and endpoints
    repo_result = await db.execute(
        select(Repository).where(Repository.id == data.repository_id)
    )
    repo = repo_result.scalar_one_or_none()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    endpoints_result = await db.execute(
        select(APIEndpoint).where(APIEndpoint.repository_id == data.repository_id)
    )
    endpoints = endpoints_result.scalars().all()
    
    # Create export job
    job = ExportJob(
        repository_id=data.repository_id,
        format=data.format,
        title=data.title or repo.name,
        version=data.version,
        base_url=data.base_url,
        include_examples=data.include_examples,
        status="processing",
        started_at=datetime.utcnow()
    )
    db.add(job)
    
    try:
        # Generate export based on format
        if data.format == "openapi_3.0":
            content = _generate_openapi(endpoints, job)
            job.output_url = f"/api/export/{job.id}/download"
        elif data.format == "postman_2.1":
            content = _generate_postman(endpoints, job)
            job.output_url = f"/api/export/{job.id}/download"
        elif data.format == "markdown":
            content = _generate_markdown(endpoints, job)
            job.output_url = f"/api/export/{job.id}/download"
        elif data.format == "html":
            content = _generate_html(endpoints, job)
            job.output_url = f"/api/export/{job.id}/download"
        
        job.status = "completed"
        job.file_size_bytes = len(content.encode())
        job.completed_at = datetime.utcnow()
        job.expires_at = datetime.utcnow() + timedelta(hours=24)
        
    except Exception as e:
        job.status = "failed"
    
    await db.commit()
    await db.refresh(job)
    
    return ExportResponse(
        id=str(job.id),
        format=job.format,
        status=job.status,
        output_url=job.output_url
    )


@router.get("/export/{job_id}/download")
async def download_export(
    job_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Download exported file."""
    result = await db.execute(
        select(ExportJob).where(ExportJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Export not found")
    
    # Get endpoints and regenerate
    endpoints_result = await db.execute(
        select(APIEndpoint).where(APIEndpoint.repository_id == job.repository_id)
    )
    endpoints = endpoints_result.scalars().all()
    
    # Generate content based on format
    if job.format == "openapi_3.0":
        content = _generate_openapi(endpoints, job)
        media_type = "application/json"
        filename = "openapi.json"
    elif job.format == "postman_2.1":
        content = _generate_postman(endpoints, job)
        media_type = "application/json"
        filename = "postman_collection.json"
    elif job.format == "markdown":
        content = _generate_markdown(endpoints, job)
        media_type = "text/markdown"
        filename = "api-docs.md"
    elif job.format == "html":
        content = _generate_html(endpoints, job)
        media_type = "text/html"
        filename = "api-docs.html"
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/jobs", response_model=List[JobResponse])
async def list_export_jobs(
    repository_id: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List export jobs."""
    query = select(ExportJob)
    
    if repository_id:
        query = query.where(ExportJob.repository_id == repository_id)
    
    query = query.order_by(desc(ExportJob.created_at)).limit(limit)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return [
        JobResponse(
            id=str(j.id),
            format=j.format,
            status=j.status,
            created_at=j.created_at
        )
        for j in jobs
    ]


# ==================== Import Helpers ====================

async def _import_openapi(spec: dict, repository_id: str, db: AsyncSession) -> tuple:
    """Import from OpenAPI/Swagger spec."""
    imported = 0
    updated = 0
    skipped = 0
    
    paths = spec.get("paths", {})
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                # Check if endpoint exists
                existing = await db.execute(
                    select(APIEndpoint).where(
                        APIEndpoint.repository_id == repository_id,
                        APIEndpoint.path == path,
                        APIEndpoint.method == method.upper()
                    )
                )
                endpoint = existing.scalar_one_or_none()
                
                if endpoint:
                    # Update existing
                    endpoint.description = details.get("summary", details.get("description", ""))
                    endpoint.tags = json.dumps(details.get("tags", []))
                    updated += 1
                else:
                    # Create new
                    endpoint = APIEndpoint(
                        repository_id=repository_id,
                        path=path,
                        method=method.upper(),
                        description=details.get("summary", details.get("description", "")),
                        tags=json.dumps(details.get("tags", [])),
                        request_body=json.dumps(details.get("requestBody", {})),
                        response_schema=json.dumps(details.get("responses", {}))
                    )
                    db.add(endpoint)
                    imported += 1
    
    return imported, updated, skipped


async def _import_postman(spec: dict, repository_id: str, db: AsyncSession) -> tuple:
    """Import from Postman collection."""
    imported = 0
    updated = 0
    skipped = 0
    
    def process_items(items, path_prefix=""):
        nonlocal imported, updated, skipped
        for item in items:
            if "item" in item:
                # It's a folder
                process_items(item["item"], f"{path_prefix}/{item.get('name', '')}")
            elif "request" in item:
                # It's a request
                request = item["request"]
                method = request.get("method", "GET")
                url = request.get("url", {})
                
                if isinstance(url, str):
                    path = url
                else:
                    path = "/" + "/".join(url.get("path", []))
                
                endpoint = APIEndpoint(
                    repository_id=repository_id,
                    path=path,
                    method=method,
                    description=item.get("name", ""),
                    request_body=json.dumps(request.get("body", {}))
                )
                db.add(endpoint)
                imported += 1
    
    items = spec.get("item", [])
    process_items(items)
    
    return imported, updated, skipped


# ==================== Export Generators ====================

def _generate_openapi(endpoints: list, job: ExportJob) -> str:
    """Generate OpenAPI 3.0 spec."""
    paths = {}
    
    for ep in endpoints:
        if ep.path not in paths:
            paths[ep.path] = {}
        
        paths[ep.path][ep.method.lower()] = {
            "summary": ep.description or "",
            "tags": json.loads(ep.tags) if ep.tags else [],
            "responses": {
                "200": {"description": "Success"}
            }
        }
    
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": job.title or "API Documentation",
            "version": job.version or "1.0.0"
        },
        "servers": [{"url": job.base_url or "/"}],
        "paths": paths
    }
    
    return json.dumps(spec, indent=2)


def _generate_postman(endpoints: list, job: ExportJob) -> str:
    """Generate Postman collection."""
    items = []
    
    for ep in endpoints:
        items.append({
            "name": ep.description or f"{ep.method} {ep.path}",
            "request": {
                "method": ep.method,
                "url": {
                    "raw": f"{{{{base_url}}}}{ep.path}",
                    "host": ["{{base_url}}"],
                    "path": ep.path.strip("/").split("/")
                }
            }
        })
    
    collection = {
        "info": {
            "name": job.title or "API Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": items,
        "variable": [
            {"key": "base_url", "value": job.base_url or "http://localhost:8000"}
        ]
    }
    
    return json.dumps(collection, indent=2)


def _generate_markdown(endpoints: list, job: ExportJob) -> str:
    """Generate Markdown documentation."""
    lines = [
        f"# {job.title or 'API Documentation'}",
        "",
        f"Version: {job.version or '1.0.0'}",
        "",
        "## Endpoints",
        ""
    ]
    
    # Group by path
    for ep in sorted(endpoints, key=lambda x: x.path):
        method_badge = {
            "GET": "🟢",
            "POST": "🟡",
            "PUT": "🟠",
            "PATCH": "🔵",
            "DELETE": "🔴"
        }.get(ep.method, "⚪")
        
        lines.append(f"### {method_badge} `{ep.method}` {ep.path}")
        lines.append("")
        
        if ep.description:
            lines.append(ep.description)
            lines.append("")
        
        if ep.request_body and job.include_examples:
            lines.append("**Request Body:**")
            lines.append("```json")
            lines.append(ep.request_body)
            lines.append("```")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def _generate_html(endpoints: list, job: ExportJob) -> str:
    """Generate HTML documentation."""
    endpoint_html = ""
    
    for ep in sorted(endpoints, key=lambda x: x.path):
        method_class = ep.method.lower()
        endpoint_html += f'''
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method {method_class}">{ep.method}</span>
                <span class="path">{ep.path}</span>
            </div>
            <p class="description">{ep.description or ""}</p>
        </div>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{job.title or "API Documentation"}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; color: #fff; margin: 0; padding: 40px; }}
        h1 {{ border-bottom: 1px solid #333; padding-bottom: 20px; }}
        .endpoint {{ background: #111; border-radius: 8px; padding: 16px; margin: 16px 0; }}
        .endpoint-header {{ display: flex; gap: 12px; align-items: center; }}
        .method {{ padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 12px; }}
        .get {{ background: #22c55e20; color: #22c55e; }}
        .post {{ background: #eab30820; color: #eab308; }}
        .put {{ background: #f9731620; color: #f97316; }}
        .delete {{ background: #ef444420; color: #ef4444; }}
        .path {{ font-family: monospace; font-size: 14px; }}
        .description {{ color: #888; margin: 8px 0 0 0; }}
    </style>
</head>
<body>
    <h1>{job.title or "API Documentation"}</h1>
    <p>Version: {job.version or "1.0.0"}</p>
    {endpoint_html}
</body>
</html>'''
