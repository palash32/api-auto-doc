import os
import ast
import shutil
import tempfile
import git
import re
from typing import List, Dict, Any
from app.models.api_endpoint import APIEndpoint
from app.core.logger import logger

class DiscoveryService:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()

    def cleanup(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def scan_repository(self, repo_url: str, repo_id: str) -> List[ApiEndpoint]:
        """Clone and scan a repository for APIs."""
        try:
            # Clone repo
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            repo_path = os.path.join(self.temp_dir, repo_name)
            
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                
            logger.info(f"Cloning {repo_url} to {repo_path}...")
            git.Repo.clone_from(repo_url, repo_path)
            
            discovered_apis = []
            
            # Walk through files
            for root, _, files in os.walk(repo_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if file.endswith(".py"):
                        apis = self._parse_python_file(file_path, repo_id)
                        discovered_apis.extend(apis)
                    elif file.endswith(".js") or file.endswith(".ts"):
                        apis = self._parse_node_file(file_path, repo_id)
                        discovered_apis.extend(apis)
                        
            return discovered_apis
            
        except Exception as e:
            logger.error(f"Error scanning repository: {e}")
            return []
        finally:
            self.cleanup()

    def _parse_python_file(self, file_path: str, repo_id: str) -> List[ApiEndpoint]:
        """Parse Python file for FastAPI/Flask/Django routes."""
        apis = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for decorators
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            # Check for FastAPI route decorators: @app.get("/path") or @router.post("/path")
                            if hasattr(decorator.func, "attr") and decorator.func.attr in ["get", "post", "put", "delete", "patch"]:
                                method = decorator.func.attr.upper()
                                path = "unknown"
                                
                                # Extract path from arguments
                                if decorator.args:
                                    if isinstance(decorator.args[0], ast.Constant): # Python 3.8+
                                        path = decorator.args[0].value
                                    elif isinstance(decorator.args[0], ast.Str): # Older Python
                                        path = decorator.args[0].s
                                
                                # Extract docstring
                                docstring = ast.get_docstring(node)
                                
                                apis.append(APIEndpoint(
                                    repository_id=str(repo_id),
                                    path=path,
                                    method=method,
                                    summary=node.name,
                                    description=docstring,
                                    status="healthy"
                                ))
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
            pass
            
        return apis

    def _parse_node_file(self, file_path: str, repo_id: str) -> List[ApiEndpoint]:
        """Parse Node.js file for Express routes (simple regex for now)."""
        apis = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Regex for Express: app.get('/path', ...) or router.post('/path', ...)
            # Matches: .get(', .post(', etc.
            pattern = r"\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
            matches = re.finditer(pattern, content)
            
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                
                apis.append(APIEndpoint(
                    repository_id=str(repo_id),
                    path=path,
                    method=method,
                    summary=f"Express {method} {path}",
                    status="healthy"
                ))
        except Exception as e:
            pass
            
        return apis

discovery_service = DiscoveryService()
