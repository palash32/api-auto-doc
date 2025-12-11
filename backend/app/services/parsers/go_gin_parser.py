"""Go Gin/Echo API endpoint parser."""

import re
from typing import List, Optional
from app.services.parsers.base_parser import BaseParser, ParsedEndpoint, ParsedParameter


class GoGinParser(BaseParser):
    """
    Parser for Go Gin and Echo framework API endpoints.
    
    Detects patterns like:
    - r.GET("/path", handler)
    - router.POST("/path", handler)
    - e.GET("/path", handler) for Echo
    - api := r.Group("/api")
    """
    
    FRAMEWORK_NAME = "go_gin"
    SUPPORTED_EXTENSIONS = [".go"]
    FRAMEWORK_INDICATORS = [
        "github.com/gin-gonic/gin",
        "github.com/labstack/echo",
        "gin.Default()",
        "gin.New()",
        "echo.New()",
        ".GET(",
        ".POST(",
        ".PUT(",
        ".DELETE("
    ]
    
    # HTTP method patterns for Gin/Echo
    METHOD_PATTERN = re.compile(
        r'(?:router|r|e|g|api|group|app)\s*\.\s*(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s*\(\s*"([^"]+)"',
        re.IGNORECASE | re.MULTILINE
    )
    
    # Group pattern for base paths
    GROUP_PATTERN = re.compile(
        r'(\w+)\s*:?=\s*\w+\s*\.\s*Group\s*\(\s*"([^"]+)"',
        re.MULTILINE
    )
    
    # Handler function pattern
    HANDLER_PATTERN = re.compile(
        r',\s*(\w+)\s*\)',
        re.MULTILINE
    )
    
    # Function definition
    FUNC_DEF = re.compile(
        r'func\s+(\w+)\s*\(',
        re.MULTILINE
    )
    
    # Param binding patterns
    PARAM_PATTERN = re.compile(
        r'c\.Param\s*\(\s*"([^"]+)"',
        re.MULTILINE
    )
    
    QUERY_PATTERN = re.compile(
        r'c\.(?:Query|DefaultQuery)\s*\(\s*"([^"]+)"',
        re.MULTILINE
    )
    
    def parse_file(self, file_path: str) -> List[ParsedEndpoint]:
        """Parse a Go Gin/Echo file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_content(content, file_path)
        except Exception as e:
            return []
    
    def parse_content(self, content: str, file_path: str = "") -> List[ParsedEndpoint]:
        """Parse Go Gin/Echo content for API endpoints."""
        endpoints = []
        
        # Find route groups for base paths
        groups = {}
        for match in self.GROUP_PATTERN.finditer(content):
            group_name = match.group(1)
            group_path = match.group(2)
            groups[group_name] = group_path
        
        # Find all route definitions
        for match in self.METHOD_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            
            line_number = content[:match.start()].count('\n') + 1
            
            # Find handler function name
            handler_search = content[match.end():match.end() + 100]
            handler_match = self.HANDLER_PATTERN.search(handler_search)
            handler_name = handler_match.group(1) if handler_match else "handler"
            
            # Normalize path
            full_path = self.normalize_path(path)
            
            # Extract path parameters (Gin uses :param syntax)
            path_params = self.extract_path_params(full_path)
            parameters = [
                ParsedParameter(name=p, param_type="path", required=True)
                for p in path_params
            ]
            
            # Try to find query parameters in handler
            handler_params = self._find_handler_params(content, handler_name)
            parameters.extend(handler_params)
            
            # Check for auth middleware
            auth_required = self._has_auth_middleware(content, match.start())
            
            endpoint = ParsedEndpoint(
                path=full_path,
                method=method,
                function_name=handler_name,
                file_path=file_path,
                line_number=line_number,
                parameters=parameters,
                auth_required=auth_required,
                tags=self._extract_tags(file_path, full_path)
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _find_handler_params(self, content: str, handler_name: str) -> List[ParsedParameter]:
        """Find query parameters used in a handler function."""
        parameters = []
        
        # Find the handler function
        pattern = re.compile(rf'func\s+{re.escape(handler_name)}\s*\([^)]*\)\s*\{{', re.MULTILINE)
        match = pattern.search(content)
        
        if not match:
            return parameters
        
        # Extract function body (simplified - look for next func or end)
        func_start = match.end()
        remaining = content[func_start:]
        next_func = re.search(r'\n\s*func\s+', remaining)
        func_body = remaining[:next_func.start()] if next_func else remaining[:1000]
        
        # Find c.Query() calls
        for qmatch in self.QUERY_PATTERN.finditer(func_body):
            param_name = qmatch.group(1)
            parameters.append(ParsedParameter(
                name=param_name,
                param_type="query",
                required=False
            ))
        
        return parameters
    
    def _has_auth_middleware(self, content: str, route_start: int) -> bool:
        """Check if route has auth middleware."""
        # Look at preceding context
        search_start = max(0, route_start - 300)
        preceding = content[search_start:route_start]
        
        auth_patterns = [
            'AuthMiddleware',
            'jwt',
            'JWT',
            'Auth(',
            'RequireAuth',
            'Authenticate'
        ]
        
        return any(pattern in preceding for pattern in auth_patterns)
    
    def _extract_tags(self, file_path: str, path: str) -> List[str]:
        """Extract tags from context."""
        tags = []
        
        # From file name
        if file_path:
            import os
            filename = os.path.basename(file_path).replace('.go', '').replace('_handler', '').replace('_controller', '')
            if filename not in ['main', 'routes', 'router']:
                tags.append(filename.title())
        
        # From path
        parts = path.strip('/').split('/')
        if parts and parts[0]:
            tag = parts[0].replace('-', ' ').replace('_', ' ').title()
            if tag not in tags:
                tags.append(tag)
        
        return tags[:2]
