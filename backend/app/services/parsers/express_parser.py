"""Express.js (Node.js) API endpoint parser."""

import re
from typing import List, Optional
from app.services.parsers.base_parser import BaseParser, ParsedEndpoint, ParsedParameter


class ExpressParser(BaseParser):
    """
    Parser for Express.js API endpoints.
    
    Detects patterns like:
    - app.get('/path', handler)
    - router.post('/path', handler)
    - app.use('/api', router)
    """
    
    FRAMEWORK_NAME = "express"
    SUPPORTED_EXTENSIONS = [".js", ".ts", ".mjs"]
    FRAMEWORK_INDICATORS = [
        "express()",
        "require('express')",
        'require("express")',
        "from 'express'",
        'from "express"',
        "express.Router()"
    ]
    
    # HTTP method patterns
    METHOD_PATTERN = re.compile(
        r'(?:app|router|server)\s*\.\s*(get|post|put|patch|delete|head|options)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        re.IGNORECASE | re.MULTILINE
    )
    
    # Route with middleware pattern
    ROUTE_WITH_MIDDLEWARE = re.compile(
        r'(?:app|router)\s*\.\s*(get|post|put|patch|delete)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*(?:[\w.]+\s*,\s*)*(?:async\s*)?\(?(?:req|request)',
        re.IGNORECASE | re.MULTILINE
    )
    
    # Router.route() pattern
    ROUTER_ROUTE_PATTERN = re.compile(
        r'\.route\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)\s*\.(get|post|put|patch|delete)',
        re.IGNORECASE | re.MULTILINE
    )
    
    # Express middleware mount pattern
    USE_PATTERN = re.compile(
        r'(?:app|router)\s*\.\s*use\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        re.IGNORECASE | re.MULTILINE
    )
    
    def parse_file(self, file_path: str) -> List[ParsedEndpoint]:
        """Parse an Express.js file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_content(content, file_path)
        except Exception as e:
            return []
    
    def parse_content(self, content: str, file_path: str = "") -> List[ParsedEndpoint]:
        """Parse Express.js content for API endpoints."""
        endpoints = []
        lines = content.split('\n')
        
        # Find base path from router use statements
        base_paths = self._find_base_paths(content)
        
        # Find all route definitions
        for match in self.METHOD_PATTERN.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            
            # Find line number
            line_number = content[:match.start()].count('\n') + 1
            
            # Extract function name from context
            func_name = self._extract_function_name(content, match.end())
            
            # Normalize path
            path = self.normalize_path(path)
            
            # Extract path parameters
            path_params = self.extract_path_params(path)
            parameters = [
                ParsedParameter(name=p, param_type="path", required=True)
                for p in path_params
            ]
            
            # Check for auth middleware
            auth_required = self._has_auth_middleware(content, match.start(), match.end())
            
            endpoint = ParsedEndpoint(
                path=path,
                method=method,
                function_name=func_name or f"{method.lower()}_{path.replace('/', '_')}",
                file_path=file_path,
                line_number=line_number,
                parameters=parameters,
                auth_required=auth_required,
                tags=self._extract_tags(file_path, path)
            )
            endpoints.append(endpoint)
        
        # Also check router.route() pattern
        for match in self.ROUTER_ROUTE_PATTERN.finditer(content):
            path = match.group(1)
            method = match.group(2).upper()
            line_number = content[:match.start()].count('\n') + 1
            
            path = self.normalize_path(path)
            path_params = self.extract_path_params(path)
            
            endpoint = ParsedEndpoint(
                path=path,
                method=method,
                function_name=f"{method.lower()}_{path.replace('/', '_').replace(':', '')}",
                file_path=file_path,
                line_number=line_number,
                parameters=[
                    ParsedParameter(name=p, param_type="path", required=True)
                    for p in path_params
                ],
                tags=self._extract_tags(file_path, path)
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _find_base_paths(self, content: str) -> List[str]:
        """Find router mount paths."""
        paths = []
        for match in self.USE_PATTERN.finditer(content):
            paths.append(match.group(1))
        return paths
    
    def _extract_function_name(self, content: str, start_pos: int) -> Optional[str]:
        """Try to extract handler function name."""
        # Look for named function after the route
        search_area = content[start_pos:start_pos + 200]
        
        # Pattern: function handler or const handler = 
        func_match = re.search(r',\s*(\w+)\s*[,)]', search_area)
        if func_match:
            return func_match.group(1)
        
        # Pattern: async (req, res) => { ... }
        arrow_match = re.search(r'async\s*\(', search_area)
        if arrow_match:
            return "anonymous_handler"
        
        return None
    
    def _has_auth_middleware(self, content: str, start: int, end: int) -> bool:
        """Check if route has authentication middleware."""
        # Look at the full route definition
        line_start = content.rfind('\n', 0, start) + 1
        line_end = content.find('\n', end)
        route_line = content[line_start:line_end] if line_end > 0 else content[line_start:]
        
        auth_patterns = [
            'auth', 'authenticate', 'isAuthenticated', 'requireAuth',
            'passport', 'jwt', 'verifyToken', 'protect', 'authorize'
        ]
        
        route_lower = route_line.lower()
        return any(pattern.lower() in route_lower for pattern in auth_patterns)
    
    def _extract_tags(self, file_path: str, path: str) -> List[str]:
        """Extract tags from file path and route."""
        tags = []
        
        # Extract from file name
        if file_path:
            import os
            filename = os.path.basename(file_path).replace('.js', '').replace('.ts', '')
            if filename not in ['index', 'routes', 'router']:
                tags.append(filename.title())
        
        # Extract from path
        parts = path.split('/')
        if len(parts) > 1 and parts[1]:
            tag = parts[1].replace('-', ' ').replace('_', ' ').title()
            if tag not in tags:
                tags.append(tag)
        
        return tags
