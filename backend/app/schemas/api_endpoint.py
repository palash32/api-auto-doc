from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.api_endpoint import HTTPMethod, APIStatus

class APIEndpointBase(BaseModel):
    path: str = Field(..., min_length=1, description="API path, e.g., /users")
    method: HTTPMethod
    summary: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    auth_required: bool = False
    auth_type: Optional[str] = None

class APIEndpointCreate(APIEndpointBase):
    repository_id: UUID
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: List[Dict[str, Any]] = Field(default_factory=list)

class APIEndpointUpdate(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[APIStatus] = None

class APIEndpointResponse(APIEndpointBase):
    id: UUID
    repository_id: UUID
    status: APIStatus
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: List[Dict[str, Any]]
    file_path: Optional[str]
    start_line: Optional[int]
    end_line: Optional[int]
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedEndpoints(BaseModel):
    total: int
    page: int
    per_page: int
    endpoints: List[APIEndpointResponse]
