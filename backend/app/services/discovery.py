"""Multi-framework API endpoint discovery service.

Supports:
- Python: FastAPI, Flask, Django REST Framework
- JavaScript/TypeScript: Express, NestJS, Fastify
- Go: Gin, Fiber, Echo
"""

import os
import ast
import shutil
import tempfile
import git
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.models.api_endpoint import APIEndpoint
from app.core.logger import logger


@dataclass
class DiscoveredEndpoint:
    """Represents a discovered API endpoint."""
    path: str
    method: str
    summary: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    framework: Optional[str] = None


class DiscoveryService:
    """Multi-framework API endpoint discovery."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()

    def cleanup(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def scan_repository(self, repo_url: str, repo_id: str) -> List[APIEndpoint]:
        """Clone and scan a repository for APIs."""
        try:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            repo_path = os.path.join(self.temp_dir, repo_name)
            
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                
            logger.info(f"Cloning {repo_url} to {repo_path}...")
            git.Repo.clone_from(repo_url, repo_path)
            
            discovered_apis = []
            
            for root, _, files in os.walk(repo_path):
                # Skip common non-source directories
                if any(skip in root for skip in ['.git', 'node_modules', '__pycache__', 'venv', 'dist']):
                    continue
                    
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, repo_path)
                    
                    try:
                        if file.endswith(".py"):
                            apis = self._parse_python_file(file_path, repo_id, relative_path)
                            discovered_apis.extend(apis)
                        elif file.endswith((".js", ".ts", ".jsx", ".tsx")):
                            apis = self._parse_node_file(file_path, repo_id, relative_path)
                            discovered_apis.extend(apis)
                        elif file.endswith(".go"):
                            apis = self._parse_go_file(file_path, repo_id, relative_path)
                            discovered_apis.extend(apis)
                    except Exception as e:
                        logger.warning(f"Error parsing {relative_path}: {e}")
                        continue
                        
            logger.info(f"Discovered {len(discovered_apis)} API endpoints")
            return discovered_apis
            
        except Exception as e:
            logger.error(f"Error scanning repository: {e}")
            return []
        finally:
            self.cleanup()

    def _parse_python_file(self, file_path: str, repo_id: str, relative_path: str) -> List[APIEndpoint]:
        """Parse Python file for FastAPI/Flask/Django routes."""
        apis = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    endpoint = self._extract_python_endpoint(node, repo_id, relative_path)
                    if endpoint:
                        apis.append(endpoint)
                        
        except SyntaxError as e:
            logger.debug(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.debug(f"Error parsing {file_path}: {e}")
            
        return apis

    def _extract_python_endpoint(self, node: ast.FunctionDef, repo_id: str, file_path: str) -> Optional[APIEndpoint]:
        """Extract endpoint info from Python function decorators."""
        for decorator in node.decorator_list:
            # Handle @app.get("/path") or @router.post("/path")
            if isinstance(decorator, ast.Call):
                method, path, framework = self._parse_python_decorator(decorator)
                if method and path:
                    docstring = ast.get_docstring(node)
                    return APIEndpoint(
                        repository_id=str(repo_id),
                        path=path,
                        method=method,
                        summary=self._format_function_name(node.name),
                        description=docstring,
                        file_path=file_path,
                        start_line=node.lineno,
                        status="healthy"
                    )
                    
            # Handle @app.route("/path", methods=["GET"])
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr == "route":
                    # Flask route without parentheses
                    pass
                    
        return None

    def _parse_python_decorator(self, decorator: ast.Call) -> tuple:
        """Parse decorator to extract method, path, and framework."""
        method = None
        path = None
        framework = None
        
        # Check for attribute-style: @app.get, @router.post, @blueprint.route
        if isinstance(decorator.func, ast.Attribute):
            attr = decorator.func.attr.lower()
            
            # FastAPI/Flask HTTP methods
            if attr in ["get", "post", "put", "delete", "patch", "head", "options"]:
                method = attr.upper()
                framework = "fastapi"  # or flask
                
            # Flask route
            elif attr == "route":
                framework = "flask"
                method = "GET"  # Default, may be overridden by methods=
                # Check for methods= argument
                for keyword in decorator.keywords:
                    if keyword.arg == "methods":
                        if isinstance(keyword.value, ast.List) and keyword.value.elts:
                            first_method = keyword.value.elts[0]
                            if isinstance(first_method, ast.Constant):
                                method = first_method.value.upper()
                                
            # Django api_view
            elif attr == "api_view":
                framework = "django"
                method = "GET"
                if decorator.args and isinstance(decorator.args[0], ast.List):
                    elts = decorator.args[0].elts
                    if elts and isinstance(elts[0], ast.Constant):
                        method = elts[0].value.upper()
                        
            # Extract path from first argument
            if decorator.args:
                first_arg = decorator.args[0]
                if isinstance(first_arg, ast.Constant):
                    path = first_arg.value
                elif isinstance(first_arg, ast.Str):  # Python 3.7
                    path = first_arg.s
                    
        return method, path, framework

    def _parse_node_file(self, file_path: str, repo_id: str, relative_path: str) -> List[APIEndpoint]:
        """Parse Node.js/TypeScript file for Express/NestJS routes."""
        apis = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Express patterns: app.get('/path', ...) or router.post('/path', ...)
            express_pattern = r"(?:app|router|express\(\))\s*\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
            for match in re.finditer(express_pattern, content, re.IGNORECASE):
                method = match.group(1).upper()
                path = match.group(2)
                apis.append(APIEndpoint(
                    repository_id=str(repo_id),
                    path=path,
                    method=method,
                    summary=f"Express {method} {path}",
                    file_path=relative_path,
                    status="healthy"
                ))
                
            # NestJS patterns: @Get('/path'), @Post(), etc.
            nestjs_pattern = r"@(Get|Post|Put|Delete|Patch)\s*\(\s*['\"]?([^'\")\s]*)['\"]?\s*\)"
            for match in re.finditer(nestjs_pattern, content):
                method = match.group(1).upper()
                path = match.group(2) or "/"
                apis.append(APIEndpoint(
                    repository_id=str(repo_id),
                    path=path,
                    method=method,
                    summary=f"NestJS {method} {path}",
                    file_path=relative_path,
                    status="healthy"
                ))
                
            # Fastify patterns: fastify.get('/path', ...)
            fastify_pattern = r"fastify\s*\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
            for match in re.finditer(fastify_pattern, content, re.IGNORECASE):
                method = match.group(1).upper()
                path = match.group(2)
                apis.append(APIEndpoint(
                    repository_id=str(repo_id),
                    path=path,
                    method=method,
                    summary=f"Fastify {method} {path}",
                    file_path=relative_path,
                    status="healthy"
                ))
                
        except Exception as e:
            logger.debug(f"Error parsing {file_path}: {e}")
            
        return apis

    def _parse_go_file(self, file_path: str, repo_id: str, relative_path: str) -> List[APIEndpoint]:
        """Parse Go file for Gin/Fiber/Echo routes."""
        apis = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Gin patterns: r.GET("/path", ...) or group.POST("/path", ...)
            gin_pattern = r"(?:r|router|group|e|app|c)\s*\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*['\"]([^'\"]+)['\"]"
            for match in re.finditer(gin_pattern, content):
                method = match.group(1).upper()
                path = match.group(2)
                apis.append(APIEndpoint(
                    repository_id=str(repo_id),
                    path=path,
                    method=method,
                    summary=f"Go API {method} {path}",
                    file_path=relative_path,
                    status="healthy"
                ))
                
            # Echo patterns: e.GET("/path", ...)
            echo_pattern = r"e\s*\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*['\"]([^'\"]+)['\"]"
            for match in re.finditer(echo_pattern, content):
                method = match.group(1).upper()
                path = match.group(2)
                apis.append(APIEndpoint(
                    repository_id=str(repo_id),
                    path=path,
                    method=method,
                    summary=f"Echo {method} {path}",
                    file_path=relative_path,
                    status="healthy"
                ))
                
        except Exception as e:
            logger.debug(f"Error parsing {file_path}: {e}")
            
        return apis

    def _format_function_name(self, name: str) -> str:
        """Convert function name to human-readable summary."""
        # Convert snake_case to Title Case
        words = name.replace("_", " ").replace("-", " ").split()
        return " ".join(word.capitalize() for word in words)


discovery_service = DiscoveryService()

