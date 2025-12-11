from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from app.models.repository import GitProvider, ScanStatus

class RepositoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=500, description="owner/repo")
    git_provider: GitProvider
    repo_url: str = Field(..., max_length=500)
    default_branch: str = Field("main", min_length=1, max_length=100)
    auto_scan_enabled: bool = True

class RepositoryCreate(RepositoryBase):
    provider_repo_id: Optional[str] = None
    access_token: Optional[str] = None

class RepositoryUpdate(BaseModel):
    default_branch: Optional[str] = None
    auto_scan_enabled: Optional[bool] = None
    scan_schedule: Optional[str] = None

class RepositoryResponse(RepositoryBase):
    id: UUID
    organization_id: UUID
    scan_status: ScanStatus
    last_scanned: Optional[datetime] = None
    last_commit_sha: Optional[str] = None
    scan_error_message: Optional[str] = None
    api_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
