"""GitHub API service for fetching repository metadata."""

import httpx
from typing import Optional, Dict
from app.core.config import settings
from app.core.logger import logger


class GitHubService:
    """Service to interact with GitHub API."""
    
    BASE_URL = "https://api.github.com"
    
    @staticmethod
    def parse_github_url(url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract owner and repo name from GitHub URL.
        
        Supports formats:
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        """
        try:
            # Handle HTTPS URLs
            if 'github.com/' in url:
                parts = url.split('github.com/')[-1].split('/')
                owner = parts[0]
                repo = parts[1].replace('.git', '') if len(parts) > 1 else None
                return owner, repo
            
            # Handle SSH URLs
            if 'git@github.com:' in url:
                parts = url.split('git@github.com:')[-1].split('/')
                owner = parts[0]
                repo = parts[1].replace('.git', '') if len(parts) > 1 else None
                return owner, repo
                
            return None, None
        except Exception:
            return None, None
    
    @staticmethod
    async def fetch_repository_info(owner: str, repo: str) -> Optional[Dict]:
        """
        Fetch repository information from GitHub API.
        
        Returns repository metadata including:
        - name, description
        - language (primary language)
        - stars, forks
        - default branch
        - created/updated dates
        """
        try:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            # Add authorization if token is available
            if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
                # For production, store personal access token in env
                pass
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{GitHubService.BASE_URL}/repos/{owner}/{repo}",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                
                return {
                    "name": data.get("name"),
                    "full_name": data.get("full_name"),
                    "description": data.get("description") or "No description provided",
                    "language": data.get("language") or "Unknown",
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "default_branch": data.get("default_branch", "main"),
                    "owner": owner,
                    "url": data.get("html_url"),
                    "clone_url": data.get("clone_url"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "is_private": data.get("private", False)
                }
                
        except Exception as e:
            logger.error(f"Error fetching GitHub repo info: {e}")
            return None


github_service = GitHubService()
