"""Service for orchestrating repository scanning and documentation generation."""

import logging
import asyncio
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.encryption import decrypt_token
from app.models.repository import Repository, ScanStatus
from app.models.api_endpoint import APIEndpoint
from app.services.git_service import GitService
from app.services.scanner import RepositoryScanner
from app.services.ai_service import GeminiService

logger = logging.getLogger(__name__)


class ScanService:
    """Orchestrator for the repository scanning pipeline."""

    def __init__(self):
        self.git_service = GitService()
        self.scanner = RepositoryScanner()
        self.ai_service = GeminiService()

    async def process_repository(self, repo_id: UUID):
        """
        Background task to process a repository.
        
        Steps:
        1. Fetch repo details
        2. Clone repo
        3. Scan files
        4. Generate docs with AI
        5. Save to DB
        6. Cleanup
        """
        logger.info(f"Starting scan for repository {repo_id}")
        
        async with AsyncSessionLocal() as db:
            try:
                # 1. Fetch Repo
                result = await db.execute(select(Repository).where(Repository.id == repo_id))
                repo = result.scalar_one_or_none()
                
                if not repo:
                    logger.error(f"Repository {repo_id} not found")
                    return

                # Update status to SCANNING
                repo.scan_status = ScanStatus.SCANNING
                repo.last_scanned = datetime.now()
                await db.commit()

                # Get token if exists
                token = None
                if repo.access_token_encrypted:
                    try:
                        token = decrypt_token(repo.access_token_encrypted)
                    except Exception as e:
                        logger.error(f"Failed to decrypt token for repo {repo_id}: {e}")
                        # Continue without token (might be public repo)

                # 2. Clone Repo
                try:
                    repo_path = await self.git_service.clone_repository(
                        repo.repo_url, 
                        repo.full_name, 
                        token
                    )
                except Exception as e:
                    await self._fail_scan(db, repo, f"Clone failed: {str(e)}")
                    return

                # 3. Scan Files
                try:
                    files = self.scanner.scan_repository(repo_path)
                    logger.info(f"Found {len(files)} files in {repo.full_name}")
                except Exception as e:
                    await self._fail_scan(db, repo, f"Scan failed: {str(e)}")
                    self.git_service.delete_repository(repo.full_name)
                    return

                # 4. Generate Docs & Save
                api_count = 0
                for file_info in files:
                    # Only process code files that might contain APIs
                    # For MVP, let's focus on Python, JS/TS, Go
                    if file_info["language"] not in ["python", "javascript", "typescript", "go", "java", "csharp"]:
                        continue

                    try:
                        content = self.scanner.get_file_content(repo_path, file_info["path"])
                        
                        # Skip empty or too small files
                        if len(content.strip()) < 50:
                            continue

                        # Generate Docs
                        doc_result = await self.ai_service.generate_doc(content, file_info["language"])
                        
                        if doc_result and doc_result.get("path"):
                            # It's an API endpoint! Save it.
                            await self._save_endpoint(db, repo.id, file_info, doc_result)
                            api_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to process file {file_info['path']}: {e}")
                        continue

                # 5. Success
                repo.scan_status = ScanStatus.COMPLETED
                repo.api_count = api_count
                repo.scan_error_message = None
                await db.commit()
                logger.info(f"Scan completed for {repo.full_name}. Found {api_count} APIs.")

            except Exception as e:
                logger.error(f"Unexpected error scanning repo {repo_id}: {e}")
                if 'repo' in locals() and repo:
                    await self._fail_scan(db, repo, f"System error: {str(e)}")
            
            finally:
                # 6. Cleanup
                if 'repo' in locals() and repo:
                    try:
                        self.git_service.delete_repository(repo.full_name)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup repo {repo.full_name}: {e}")

    async def _fail_scan(self, db: AsyncSession, repo: Repository, error: str):
        """Helper to mark scan as failed."""
        repo.scan_status = ScanStatus.FAILED
        repo.scan_error_message = error
        await db.commit()
        logger.error(f"Scan failed for {repo.full_name}: {error}")

    async def _save_endpoint(self, db: AsyncSession, repo_id: UUID, file_info: dict, doc: dict):
        """Save a discovered endpoint to the database."""
        # Check if endpoint already exists (update if so)
        # For MVP, simple path+method check
        path = doc.get("path", "")
        method = doc.get("method", "GET").upper()
        
        stmt = select(APIEndpoint).where(
            APIEndpoint.repository_id == repo_id,
            APIEndpoint.path == path,
            APIEndpoint.method == method
        )
        result = await db.execute(stmt)
        endpoint = result.scalar_one_or_none()
        
        if not endpoint:
            endpoint = APIEndpoint(
                repository_id=repo_id,
                path=path,
                method=method
            )
            db.add(endpoint)
        
        # Update fields
        endpoint.summary = doc.get("summary", "")
        endpoint.description = doc.get("description", "")
        endpoint.tags = doc.get("tags", [])
        endpoint.parameters = doc.get("parameters", [])
        endpoint.request_body = doc.get("request_body", {})
        endpoint.responses = doc.get("responses", [])
        endpoint.auth_required = doc.get("auth_required", False)
        endpoint.auth_type = doc.get("auth_type")
        
        # Code location
        endpoint.file_path = file_info["path"]
        
        await db.commit()
