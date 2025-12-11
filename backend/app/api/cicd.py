"""CI/CD integration API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.cicd import CIPipeline, CIBuild, PRComment, BuildBadge

router = APIRouter()


# ==================== Pydantic Schemas ====================

class PipelineCreate(BaseModel):
    repository_id: str
    provider: str  # github_actions, gitlab_ci, jenkins
    name: str
    trigger_on_push: bool = True
    trigger_on_pr: bool = True
    trigger_branches: List[str] = ["main", "master"]
    pr_comments: bool = True
    fail_on_breaking_changes: bool = False


class PipelineResponse(BaseModel):
    id: str
    repository_id: str
    provider: str
    name: str
    config_file: Optional[str]
    trigger_on_push: bool
    trigger_on_pr: bool
    pr_comments: bool
    is_enabled: bool
    last_run_at: Optional[datetime]
    last_run_status: Optional[str]


class BuildResponse(BaseModel):
    id: str
    build_number: int
    commit_sha: Optional[str]
    branch: Optional[str]
    pr_number: Optional[int]
    status: str
    endpoints_found: int
    endpoints_added: int
    endpoints_modified: int
    endpoints_removed: int
    breaking_changes: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_seconds: Optional[int]


class TriggerBuildRequest(BaseModel):
    commit_sha: Optional[str] = None
    branch: str = "main"
    pr_number: Optional[int] = None


class PRCommentResponse(BaseModel):
    id: str
    pr_number: int
    has_breaking_changes: bool
    summary: Optional[dict]
    posted_at: Optional[datetime]


# ==================== Pipeline Endpoints ====================

@router.get("/cicd/pipelines", response_model=List[PipelineResponse])
async def list_pipelines(
    repository_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List CI/CD pipelines."""
    query = select(CIPipeline)
    
    if repository_id:
        query = query.where(CIPipeline.repository_id == repository_id)
    
    query = query.order_by(desc(CIPipeline.created_at))
    
    result = await db.execute(query)
    pipelines = result.scalars().all()
    
    return [
        PipelineResponse(
            id=str(p.id),
            repository_id=str(p.repository_id),
            provider=p.provider,
            name=p.name,
            config_file=p.config_file,
            trigger_on_push=p.trigger_on_push,
            trigger_on_pr=p.trigger_on_pr,
            pr_comments=p.pr_comments,
            is_enabled=p.is_enabled,
            last_run_at=p.last_run_at,
            last_run_status=p.last_run_status
        )
        for p in pipelines
    ]


@router.post("/cicd/pipelines", response_model=PipelineResponse)
async def create_pipeline(
    data: PipelineCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a CI/CD pipeline."""
    # Generate config file path based on provider
    config_files = {
        "github_actions": ".github/workflows/apidoc.yml",
        "gitlab_ci": ".gitlab-ci.yml",
        "jenkins": "Jenkinsfile",
        "bitbucket": "bitbucket-pipelines.yml",
        "circle_ci": ".circleci/config.yml"
    }
    
    pipeline = CIPipeline(
        repository_id=data.repository_id,
        provider=data.provider,
        name=data.name,
        config_file=config_files.get(data.provider),
        trigger_on_push=data.trigger_on_push,
        trigger_on_pr=data.trigger_on_pr,
        trigger_branches=data.trigger_branches,
        pr_comments=data.pr_comments,
        fail_on_breaking_changes=data.fail_on_breaking_changes
    )
    
    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)
    
    return PipelineResponse(
        id=str(pipeline.id),
        repository_id=str(pipeline.repository_id),
        provider=pipeline.provider,
        name=pipeline.name,
        config_file=pipeline.config_file,
        trigger_on_push=pipeline.trigger_on_push,
        trigger_on_pr=pipeline.trigger_on_pr,
        pr_comments=pipeline.pr_comments,
        is_enabled=pipeline.is_enabled,
        last_run_at=pipeline.last_run_at,
        last_run_status=pipeline.last_run_status
    )


@router.get("/cicd/pipelines/{pipeline_id}/config")
async def get_pipeline_config(
    pipeline_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get generated CI config file content."""
    result = await db.execute(
        select(CIPipeline).where(CIPipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Generate config based on provider
    if pipeline.provider == "github_actions":
        config = _generate_github_actions_config(pipeline)
    elif pipeline.provider == "gitlab_ci":
        config = _generate_gitlab_ci_config(pipeline)
    elif pipeline.provider == "jenkins":
        config = _generate_jenkins_config(pipeline)
    else:
        config = "# Config generation not available for this provider"
    
    return {"config_file": pipeline.config_file, "content": config}


@router.delete("/cicd/pipelines/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a pipeline."""
    result = await db.execute(
        select(CIPipeline).where(CIPipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    await db.delete(pipeline)
    await db.commit()
    
    return {"message": "Pipeline deleted"}


# ==================== Build Endpoints ====================

@router.get("/cicd/builds", response_model=List[BuildResponse])
async def list_builds(
    pipeline_id: Optional[str] = None,
    repository_id: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List builds."""
    query = select(CIBuild)
    
    if pipeline_id:
        query = query.where(CIBuild.pipeline_id == pipeline_id)
    if repository_id:
        query = query.where(CIBuild.repository_id == repository_id)
    
    query = query.order_by(desc(CIBuild.created_at)).limit(limit)
    
    result = await db.execute(query)
    builds = result.scalars().all()
    
    return [
        BuildResponse(
            id=str(b.id),
            build_number=b.build_number,
            commit_sha=b.commit_sha,
            branch=b.branch,
            pr_number=b.pr_number,
            status=b.status,
            endpoints_found=b.endpoints_found,
            endpoints_added=b.endpoints_added,
            endpoints_modified=b.endpoints_modified,
            endpoints_removed=b.endpoints_removed,
            breaking_changes=b.breaking_changes,
            started_at=b.started_at,
            finished_at=b.finished_at,
            duration_seconds=b.duration_seconds
        )
        for b in builds
    ]


@router.post("/cicd/pipelines/{pipeline_id}/trigger", response_model=BuildResponse)
async def trigger_build(
    pipeline_id: str,
    data: TriggerBuildRequest,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Manually trigger a build."""
    result = await db.execute(
        select(CIPipeline).where(CIPipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Get next build number
    count_result = await db.execute(
        select(func.count(CIBuild.id)).where(CIBuild.pipeline_id == pipeline_id)
    )
    count = count_result.scalar() or 0
    
    build = CIBuild(
        pipeline_id=pipeline_id,
        repository_id=pipeline.repository_id,
        build_number=count + 1,
        commit_sha=data.commit_sha,
        branch=data.branch,
        pr_number=data.pr_number,
        status="pending",
        started_at=datetime.utcnow()
    )
    
    db.add(build)
    
    # Update pipeline last run
    pipeline.last_run_at = datetime.utcnow()
    pipeline.last_run_status = "pending"
    
    await db.commit()
    await db.refresh(build)
    
    return BuildResponse(
        id=str(build.id),
        build_number=build.build_number,
        commit_sha=build.commit_sha,
        branch=build.branch,
        pr_number=build.pr_number,
        status=build.status,
        endpoints_found=build.endpoints_found,
        endpoints_added=build.endpoints_added,
        endpoints_modified=build.endpoints_modified,
        endpoints_removed=build.endpoints_removed,
        breaking_changes=build.breaking_changes,
        started_at=build.started_at,
        finished_at=build.finished_at,
        duration_seconds=build.duration_seconds
    )


# ==================== PR Comments ====================

@router.get("/cicd/pr-comments", response_model=List[PRCommentResponse])
async def list_pr_comments(
    repository_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List PR comments."""
    result = await db.execute(
        select(PRComment)
        .where(PRComment.repository_id == repository_id)
        .order_by(desc(PRComment.created_at))
        .limit(limit)
    )
    comments = result.scalars().all()
    
    return [
        PRCommentResponse(
            id=str(c.id),
            pr_number=c.pr_number,
            has_breaking_changes=c.has_breaking_changes,
            summary=c.summary,
            posted_at=c.posted_at
        )
        for c in comments
    ]


# ==================== Build Badges ====================

@router.get("/cicd/badge/{repository_id}")
async def get_badge(
    repository_id: str,
    type: str = "status",  # status, endpoints, coverage
    db: AsyncSession = Depends(get_async_db)
):
    """Get build badge SVG for a repository."""
    result = await db.execute(
        select(BuildBadge).where(BuildBadge.repository_id == repository_id)
    )
    badge = result.scalar_one_or_none()
    
    # Default values
    label = "API Docs"
    message = "unknown"
    color = "gray"
    
    if badge:
        label = badge.label
        if type == "status":
            message = badge.status
            color = "brightgreen" if badge.status == "passing" else "red" if badge.status == "failing" else "gray"
        elif type == "endpoints":
            message = str(badge.endpoint_count)
            color = "blue"
        elif type == "coverage" and badge.coverage_percentage:
            message = f"{badge.coverage_percentage:.0f}%"
            color = "brightgreen" if badge.coverage_percentage >= 80 else "yellow" if badge.coverage_percentage >= 50 else "red"
    
    # Generate shields.io compatible badge
    svg = _generate_badge_svg(label, message, color)
    
    return Response(content=svg, media_type="image/svg+xml")


@router.post("/cicd/badge/{repository_id}/refresh")
async def refresh_badge(
    repository_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Refresh badge status."""
    result = await db.execute(
        select(BuildBadge).where(BuildBadge.repository_id == repository_id)
    )
    badge = result.scalar_one_or_none()
    
    if not badge:
        badge = BuildBadge(repository_id=repository_id)
        db.add(badge)
    
    # Get latest build status
    build_result = await db.execute(
        select(CIBuild)
        .where(CIBuild.repository_id == repository_id)
        .order_by(desc(CIBuild.created_at))
        .limit(1)
    )
    latest_build = build_result.scalar_one_or_none()
    
    if latest_build:
        badge.status = "passing" if latest_build.status == "success" else "failing" if latest_build.status == "failed" else "unknown"
        badge.endpoint_count = latest_build.endpoints_found
    
    badge.last_updated = datetime.utcnow()
    await db.commit()
    
    return {"message": "Badge refreshed", "status": badge.status}


# ==================== Config Generators ====================

def _generate_github_actions_config(pipeline: CIPipeline) -> str:
    """Generate GitHub Actions workflow file."""
    branches = pipeline.trigger_branches or ["main"]
    
    return f"""name: {pipeline.name}

on:
  push:
    branches: {branches}
  pull_request:
    branches: {branches}

jobs:
  scan-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Scan API Endpoints
        uses: apidoc/scan-action@v1
        with:
          api-key: ${{{{ secrets.APIDOC_API_KEY }}}}
          repository-id: {pipeline.repository_id}
          
      - name: Comment on PR
        if: github.event_name == 'pull_request' && {str(pipeline.pr_comments).lower()}
        uses: apidoc/pr-comment-action@v1
        with:
          api-key: ${{{{ secrets.APIDOC_API_KEY }}}}
          fail-on-breaking: {str(pipeline.fail_on_breaking_changes).lower()}
"""


def _generate_gitlab_ci_config(pipeline: CIPipeline) -> str:
    """Generate GitLab CI config file."""
    return f"""stages:
  - scan

scan-api:
  stage: scan
  image: apidoc/scanner:latest
  script:
    - apidoc scan --api-key $APIDOC_API_KEY --repo-id {pipeline.repository_id}
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
"""


def _generate_jenkins_config(pipeline: CIPipeline) -> str:
    """Generate Jenkinsfile."""
    return f"""pipeline {{
    agent any
    
    environment {{
        APIDOC_API_KEY = credentials('apidoc-api-key')
    }}
    
    stages {{
        stage('Scan API') {{
            steps {{
                sh 'apidoc scan --api-key $APIDOC_API_KEY --repo-id {pipeline.repository_id}'
            }}
        }}
    }}
    
    post {{
        always {{
            apidocPublishReport()
        }}
    }}
}}
"""


def _generate_badge_svg(label: str, message: str, color: str) -> str:
    """Generate a shields.io style badge SVG."""
    colors = {
        "brightgreen": "#4c1",
        "green": "#97ca00",
        "yellow": "#dfb317",
        "orange": "#fe7d37",
        "red": "#e05d44",
        "blue": "#007ec6",
        "gray": "#555"
    }
    bg_color = colors.get(color, colors["gray"])
    
    label_width = len(label) * 7 + 10
    message_width = len(message) * 7 + 10
    total_width = label_width + message_width
    
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{message_width}" height="20" fill="{bg_color}"/>
    <rect width="{total_width}" height="20" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_width/2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width/2}" y="14">{label}</text>
    <text x="{label_width + message_width/2}" y="15" fill="#010101" fill-opacity=".3">{message}</text>
    <text x="{label_width + message_width/2}" y="14">{message}</text>
  </g>
</svg>'''
