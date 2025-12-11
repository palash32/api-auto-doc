"""Webhook service for processing GitHub events."""

import hmac
import hashlib
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import logger
from app.models.repository import Repository


def validate_github_signature(
    payload: bytes,
    signature_header: str,
    secret: str
) -> bool:
    """
    Validate GitHub webhook signature (X-Hub-Signature-256).
    
    Args:
        payload: Raw request body bytes
        signature_header: Value of X-Hub-Signature-256 header
        secret: Webhook secret configured in GitHub
    
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    
    expected_signature = signature_header[7:]  # Remove "sha256=" prefix
    
    computed = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed, expected_signature)


def parse_push_event(payload: dict) -> Optional[dict]:
    """
    Parse GitHub push event payload.
    
    Returns:
        Dict with repo_full_name, branch, commits, sender, or None if invalid
    """
    try:
        ref = payload.get("ref", "")
        
        # Extract branch name from ref (refs/heads/main -> main)
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else None
        
        if not branch:
            return None
        
        repo = payload.get("repository", {})
        
        return {
            "repo_full_name": repo.get("full_name"),
            "repo_clone_url": repo.get("clone_url"),
            "branch": branch,
            "commits": payload.get("commits", []),
            "commit_count": len(payload.get("commits", [])),
            "head_commit": payload.get("head_commit", {}),
            "sender": payload.get("sender", {}).get("login"),
            "pusher": payload.get("pusher", {}).get("name")
        }
    except Exception as e:
        logger.error(f"Failed to parse push event: {e}")
        return None


def parse_pull_request_event(payload: dict) -> Optional[dict]:
    """
    Parse GitHub pull request event payload.
    
    Returns:
        Dict with PR info or None if invalid
    """
    try:
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})
        
        return {
            "action": action,  # opened, closed, synchronize, etc.
            "repo_full_name": repo.get("full_name"),
            "pr_number": payload.get("number"),
            "pr_title": pr.get("title"),
            "pr_branch": pr.get("head", {}).get("ref"),
            "base_branch": pr.get("base", {}).get("ref"),
            "sender": payload.get("sender", {}).get("login"),
            "merged": pr.get("merged", False)
        }
    except Exception as e:
        logger.error(f"Failed to parse PR event: {e}")
        return None


async def find_repository_by_github_url(
    db: AsyncSession,
    repo_full_name: str
) -> Optional[Repository]:
    """
    Find a repository in our database by GitHub full name.
    
    Args:
        db: Database session
        repo_full_name: e.g., "owner/repo-name"
    
    Returns:
        Repository model or None
    """
    result = await db.execute(
        select(Repository).where(Repository.full_name == repo_full_name)
    )
    return result.scalar_one_or_none()


def should_trigger_rescan(
    repository: Repository,
    branch: str,
    payload: dict
) -> Tuple[bool, str]:
    """
    Determine if a push should trigger a rescan.
    
    Args:
        repository: Repository model
        branch: Branch that was pushed to
        payload: Parsed push event data
    
    Returns:
        Tuple of (should_rescan, reason)
    """
    # Check if auto-rescan is enabled
    if not getattr(repository, 'auto_scan', True):
        return False, "Auto-scan disabled for this repository"
    
    # Check if this is the default/watched branch
    watched_branches = getattr(repository, 'watched_branches', None) or [repository.default_branch]
    
    if isinstance(watched_branches, str):
        try:
            import json
            watched_branches = json.loads(watched_branches)
        except:
            watched_branches = [repository.default_branch]
    
    if branch not in watched_branches:
        return False, f"Branch '{branch}' not in watched branches: {watched_branches}"
    
    # Check commit count (skip empty pushes)
    if payload.get("commit_count", 0) == 0:
        return False, "No commits in push"
    
    return True, "All conditions met"


def extract_changed_files(payload: dict) -> list:
    """
    Extract list of changed files from push payload.
    
    Returns:
        List of file paths that were added, modified, or removed
    """
    changed_files = set()
    
    for commit in payload.get("commits", []):
        changed_files.update(commit.get("added", []))
        changed_files.update(commit.get("modified", []))
        changed_files.update(commit.get("removed", []))
    
    return list(changed_files)


def filter_api_relevant_files(files: list) -> list:
    """
    Filter files to only those likely to contain API definitions.
    
    Returns:
        List of API-relevant file paths
    """
    api_patterns = [
        # Python
        ".py",
        # JavaScript/TypeScript
        ".js", ".ts", ".jsx", ".tsx",
        # API definition files
        "routes", "api", "endpoints", "controller", "handler",
        # Config files that might affect APIs
        "openapi", "swagger"
    ]
    
    relevant = []
    for f in files:
        f_lower = f.lower()
        if any(pattern in f_lower for pattern in api_patterns):
            relevant.append(f)
    
    return relevant
