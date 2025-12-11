"""Git operations service for cloning and updating repositories."""

import os
import shutil
import logging
import time
from pathlib import Path
from typing import Optional
from git import Repo, GitCommandError

from app.core.config import settings

logger = logging.getLogger(__name__)


class GitService:
    """Service for handling Git repository operations."""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize GitService.
        
        Args:
            storage_path: Directory to store cloned repositories. 
                          Defaults to settings.REPO_STORAGE_PATH.
        """
        self.storage_path = Path(storage_path or settings.REPO_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_repo_path(self, repo_name: str) -> Path:
        """Get local path for a repository."""
        # Sanitize repo name to prevent path traversal
        safe_name = repo_name.replace("/", "_").replace("\\", "_")
        return self.storage_path / safe_name

    async def clone_repository(self, repo_url: str, repo_name: str, token: Optional[str] = None) -> Path:
        """
        Clone a repository to local storage.
        
        Args:
            repo_url: URL of the repository
            repo_name: Name of the repository (e.g., "owner/repo")
            token: Optional OAuth token for private repos
            
        Returns:
            Path to the cloned repository
        """
        local_path = self._get_repo_path(repo_name)
        
        # Inject token into URL if provided
        auth_url = repo_url
        if token:
            # Handle https://github.com/user/repo.git -> https://oauth2:TOKEN@github.com/user/repo.git
            if "https://" in repo_url:
                auth_url = repo_url.replace("https://", f"https://oauth2:{token}@")
        
        try:
            # On Windows, if repo exists and might be locked, delete with retry first
            if local_path.exists():
                logger.info(f"Repository {repo_name} already exists. Cleaning up before fresh clone...")
                self._safe_delete(local_path)
            
            logger.info(f"Cloning {repo_name} to {local_path}...")
            Repo.clone_from(auth_url, local_path, depth=1)  # Shallow clone for speed
            return local_path
            
        except GitCommandError as e:
            logger.error(f"Failed to clone repository {repo_name}: {e}")
            # Clean up partial clone if failed
            self._safe_delete(local_path)
            raise RuntimeError(f"Git clone failed: {e}")

    async def update_repository(self, repo_name: str) -> Path:
        """
        Pull latest changes for an existing repository.
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            Path to the updated repository
        """
        local_path = self._get_repo_path(repo_name)
        
        if not local_path.exists():
            raise FileNotFoundError(f"Repository {repo_name} not found at {local_path}")
            
        try:
            repo = Repo(local_path)
            origin = repo.remotes.origin
            origin.pull()
            logger.info(f"Updated repository {repo_name}")
            return local_path
            
        except GitCommandError as e:
            logger.error(f"Failed to update repository {repo_name}: {e}")
            raise RuntimeError(f"Git pull failed: {e}")

    def delete_repository(self, repo_name: str) -> None:
        """
        Delete a cloned repository from disk.
        
        Args:
            repo_name: Name of the repository
        """
        local_path = self._get_repo_path(repo_name)
        self._safe_delete(local_path)

    def _safe_delete(self, path: Path, max_retries: int = 3) -> None:
        """
        Safely delete a directory with retry for Windows file locking issues.
        
        Args:
            path: Path to delete
            max_retries: Number of retries before giving up
        """
        if not path.exists():
            return
            
        def on_rm_error(func, path_str, exc_info):
            """Error handler that tries to fix permissions and retry."""
            try:
                os.chmod(path_str, 0o777)
                func(path_str)
            except Exception:
                pass
        
        for attempt in range(max_retries):
            try:
                # Try to remove with error handler
                shutil.rmtree(path, onerror=on_rm_error)
                logger.info(f"Deleted {path}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    # Wait with exponential backoff
                    wait_time = 0.5 * (2 ** attempt)
                    logger.warning(f"Failed to delete {path} (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to delete {path} after {max_retries} attempts: {e}")
                    # Use ignore_errors as last resort
                    shutil.rmtree(path, ignore_errors=True)
