"""GitHub webhook endpoints."""

import hmac
import hashlib
import json
import logging
from typing import Any, Dict
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_async_db
from app.models.repository import Repository, ScanStatus
from app.services.scan_service import ScanService

router = APIRouter()
scan_service = ScanService()
logger = logging.getLogger(__name__)


def verify_github_signature(payload: bytes, signature: str) -> bool:
    """
    Verify GitHub webhook signature.
    
    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header value
        
    Returns:
        True if signature is valid
    """
    if not settings.GITHUB_WEBHOOK_SECRET:
        logger.warning("GITHUB_WEBHOOK_SECRET not configured. Skipping signature verification (INSECURE!)")
        return True  # For development only
        
    if not signature:
        logger.warning("No signature header provided")
        return False
        
    # Extract the hash from "sha256=<hash>"
    if not signature.startswith("sha256="):
        logger.warning(f"Invalid signature format: {signature[:20]}...")
        return False
        
    received_hash = signature[7:]
    
    # Calculate expected hash
    secret = settings.GITHUB_WEBHOOK_SECRET.encode()
    expected_hash = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    
    # Debug logging
    logger.debug(f"Received hash: {received_hash[:16]}...")
    logger.debug(f"Expected hash: {expected_hash[:16]}...")
    
    # Constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(received_hash, expected_hash)
    logger.debug(f"Signature valid: {is_valid}")
    return is_valid


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle GitHub webhook events.
    
    Supports:
    - push: Trigger repository scan
    - ping: Respond OK
    """
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    event_type = request.headers.get("X-GitHub-Event", "")
    
    # Verify signature
    if not verify_github_signature(body, signature):
        logger.warning(f"Invalid webhook signature for event: {event_type}")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse event (decode body as JSON)
    try:
        payload = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError:
        logger.error("Failed to parse webhook payload as JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    logger.info(f"Received GitHub webhook: {event_type}")
    
    # Handle ping event (no DB needed)
    if event_type == "ping":
        return {"message": "pong"}
    
    # Handle push event (DB needed for this)
    if event_type == "push":
        repo_full_name = payload.get("repository", {}).get("full_name")
        
        if not repo_full_name:
            logger.warning("Push event missing repository full_name")
            return {"message": "ignored"}
        
        # Get DB connection only when needed
        async for db in get_async_db():
            # Find repository in database
            result = await db.execute(
                select(Repository).where(Repository.full_name == repo_full_name)
            )
            repo = result.scalar_one_or_none()
            
            if not repo:
                logger.info(f"Repository {repo_full_name} not found in database")
                return {"message": "repository not tracked"}
            
            # Check if auto-scan is enabled
            if not repo.auto_scan_enabled:
                logger.info(f"Auto-scan disabled for {repo_full_name}")
                return {"message": "auto-scan disabled"}
            
            # Trigger scan
            logger.info(f"Triggering scan for {repo_full_name} (push event)")
            repo.scan_status = ScanStatus.PENDING
            await db.commit()
            
            background_tasks.add_task(scan_service.process_repository, repo.id)
            
            return {
                "message": "scan triggered",
                "repository": repo_full_name
            }
    
    # Ignore other events
    return {"message": "event ignored"}
