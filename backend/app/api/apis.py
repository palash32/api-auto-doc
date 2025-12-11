from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

router = APIRouter()

# Mock Data
APIS = [
    { 
        "id": 1, 
        "method": "GET", 
        "path": "/api/users", 
        "summary": "List all users", 
        "status": "healthy", 
        "latency": "45ms", 
        "auth": "Bearer",
        "tags": ["Users", "Public"]
    },
    { 
        "id": 2, 
        "method": "POST", 
        "path": "/api/auth/login", 
        "summary": "Authenticate user", 
        "status": "healthy", 
        "latency": "120ms", 
        "auth": "None",
        "tags": ["Auth"]
    },
    { 
        "id": 3, 
        "method": "GET", 
        "path": "/api/projects/{id}", 
        "summary": "Get project details", 
        "status": "warning", 
        "latency": "350ms", 
        "auth": "Bearer",
        "tags": ["Projects"]
    },
    { 
        "id": 4, 
        "method": "DELETE", 
        "path": "/api/users/{id}", 
        "summary": "Delete user account", 
        "status": "healthy", 
        "latency": "85ms", 
        "auth": "Admin",
        "tags": ["Users", "Admin"]
    },
    { 
        "id": 5, 
        "method": "PUT", 
        "path": "/api/settings", 
        "summary": "Update system settings", 
        "status": "error", 
        "latency": "800ms", 
        "auth": "Admin",
        "tags": ["Settings"]
    },
    { 
        "id": 6, 
        "method": "POST", 
        "path": "/api/webhooks/stripe", 
        "summary": "Handle Stripe events", 
        "status": "healthy", 
        "latency": "60ms", 
        "auth": "Signature",
        "tags": ["Webhooks", "Billing"]
    },
]

@router.get("/", response_model=List[dict])
async def get_apis():
    """Get all discovered APIs."""
    return APIS
