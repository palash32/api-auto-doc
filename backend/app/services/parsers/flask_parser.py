"""Flask API endpoint parser."""

import re
from typing import List, Optional, Tuple
from app.services.parsers.base_parser import BaseParser, ParsedEndpoint, ParsedParameter


class FlaskParser(BaseParser):
    """
    Parser for Flask API endpoints.
    
    Detects patterns like:
    - @app.route('/path', methods=['GET'])
    - @blueprint.route('/path')
    - @app.get('/path')  # Flask 2.0+
    """
    
    FRAMEWORK_NAME = "flask"
    SUPPORTED_EXTENSIONS = [".py"]
    FRAMEWORK_INDICATORS = [
        "from flask import",
        "from flask_restful import",
        "Flask(__name__)",
        "@app.route",
        "@blueprint.route",
        "flask.Blueprint"
    ]
    
    # Classic @app.route decorator
    ROUTE_DECORATOR = re.compile(
        r'@(\w+)\s*\.\s*route\s*\(\s*[\'"]([^\'"]+)[\'"]\s*(?:,\s*methods\s*=\s*\[([^\]]+)\])?\s*\)',
        re.MULTILINE
    )
    
    # Flask 2.0+ shorthand decorators
    SHORTHAND_DECORATOR = re.compile(
        r'@(\w+)\s*\.\s*(get|post|put|patch|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        re.MULTILINE
    )
    
    # Function definition following decorator
    FUNCTION_DEF = re.compile(
        r'def\s+(\w+)\s*\(',
        re.MULTILINE
    )
    
    # Docstring pattern
    DOCSTRING = re.compile(
        r'"""(.*?)"""',
        re.DOTALL
    )
    
    def parse_file(self, file_path: str) -> List[ParsedEndpoint]:
        """Parse a Flask file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_content(content, file_path)
        except Exception as e:
            return []
    
    def parse_content(self, content: str, file_path: str = "") -> List[ParsedEndpoint]:
        """Parse Flask content for API endpoints."""
        endpoints = []
        
        # Find blueprint definitions for base paths
        blueprints = self._find_blueprints(content)
        
        # Parse classic route decorators
        for match in self.ROUTE_DECORATOR.finditer(content):
            app_or_bp = match.group(1)
            path = match.group(2)
            methods_str = match.group(3)
            
            # Parse methods
            methods = self._parse_methods(methods_str) if methods_str else ["GET"]
            
            # Find function name and docstring
            func_info = self._find_function_after(content, match.end())
            if not func_info:
                continue
                
            func_name, func_start, func_end = func_info
            line_number = content[:match.start()].count('\n') + 1
            
            # Extract docstring for description
            description = self._extract_docstring(content, func_start, func_end)
            
            # Normalize path
            path = self.normalize_path(path)
            
            # Path parameters
            path_params = self.extract_path_params(path)
            parameters = [
                ParsedParameter(name=p, param_type="path", required=True)
                for p in path_params
            ]
            
            # Add query/form parameters from function args
            params_from_code = self._extract_request_params(content, func_start, func_end)
            parameters.extend(params_from_code)
            
            # Check auth decorators
            auth_required = self._has_auth_decorator(content, match.start())
            
            # Create endpoint for each method
            for method in methods:
                endpoint = ParsedEndpoint(
                    path=path,
                    method=method,
                    function_name=func_name,
                    file_path=file_path,
                    line_number=line_number,
                    description=description,
                    parameters=parameters.copy(),
                    auth_required=auth_required,
                    tags=self._extract_tags(file_path, path, blueprints.get(app_or_bp))
                )
                endpoints.append(endpoint)
        
        # Parse Flask 2.0+ shorthand decorators
        for match in self.SHORTHAND_DECORATOR.finditer(content):
            app_or_bp = match.group(1)
            method = match.group(2).upper()
            path = match.group(3)
            
            func_info = self._find_function_after(content, match.end())
            if not func_info:
                continue
                
            func_name, func_start, func_end = func_info
            line_number = content[:match.start()].count('\n') + 1
            
            path = self.normalize_path(path)
            path_params = self.extract_path_params(path)
            description = self._extract_docstring(content, func_start, func_end)
            
            endpoint = ParsedEndpoint(
                path=path,
                method=method,
                function_name=func_name,
                file_path=file_path,
                line_number=line_number,
                description=description,
                parameters=[
                    ParsedParameter(name=p, param_type="path", required=True)
                    for p in path_params
                ],
                auth_required=self._has_auth_decorator(content, match.start()),
                tags=self._extract_tags(file_path, path, blueprints.get(app_or_bp))
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_methods(self, methods_str: str) -> List[str]:
        """Parse methods from methods=['GET', 'POST'] string."""
        methods = re.findall(r'[\'"](\w+)[\'"]', methods_str)
        return [m.upper() for m in methods]
    
    def _find_blueprints(self, content: str) -> dict:
        """Find blueprint definitions and their URL prefixes."""
        blueprints = {}
        
        # Pattern: bp = Blueprint('name', __name__, url_prefix='/api')
        bp_pattern = re.compile(
            r'(\w+)\s*=\s*(?:flask\.)?Blueprint\s*\([^)]*url_prefix\s*=\s*[\'"]([^\'"]+)[\'"]',
            re.MULTILINE
        )
        
        for match in bp_pattern.finditer(content):
            bp_name = match.group(1)
            prefix = match.group(2)
            blueprints[bp_name] = prefix
        
        return blueprints
    
    def _find_function_after(self, content: str, start_pos: int) -> Optional[Tuple[str, int, int]]:
        """Find the function definition following a decorator."""
        # Look for next function definition
        search_area = content[start_pos:start_pos + 500]
        match = self.FUNCTION_DEF.search(search_area)
        
        if match:
            func_name = match.group(1)
            func_start = start_pos + match.start()
            
            # Find function end (next function or class definition)
            remaining = content[start_pos + match.end():]
            next_def = re.search(r'\n(?:def |class |@)', remaining)
            func_end = start_pos + match.end() + (next_def.start() if next_def else len(remaining))
            
            return func_name, func_start, func_end
        
        return None
    
    def _extract_docstring(self, content: str, func_start: int, func_end: int) -> str:
        """Extract docstring from function."""
        func_content = content[func_start:func_end]
        match = self.DOCSTRING.search(func_content)
        
        if match:
            docstring = match.group(1).strip()
            # Return first line only for summary
            return docstring.split('\n')[0].strip()
        
        return ""
    
    def _extract_request_params(self, content: str, func_start: int, func_end: int) -> List[ParsedParameter]:
        """Extract parameters from request.args, request.form, etc."""
        params = []
        func_content = content[func_start:func_end]
        
        # request.args.get('param')
        args_pattern = re.compile(r'request\.args\.get\([\'"](\w+)[\'"]')
        for match in args_pattern.finditer(func_content):
            params.append(ParsedParameter(
                name=match.group(1),
                param_type="query",
                required=False
            ))
        
        # request.form.get('param')
        form_pattern = re.compile(r'request\.form\.get\([\'"](\w+)[\'"]')
        for match in form_pattern.finditer(func_content):
            params.append(ParsedParameter(
                name=match.group(1),
                param_type="body",
                required=False
            ))
        
        return params
    
    def _has_auth_decorator(self, content: str, route_start: int) -> bool:
        """Check for auth decorators above the route."""
        # Look at decorators before this one
        search_start = max(0, route_start - 500)
        preceding = content[search_start:route_start]
        
        auth_patterns = [
            '@login_required',
            '@auth_required',
            '@jwt_required',
            '@token_required',
            '@requires_auth',
            '@authenticate'
        ]
        
        return any(pattern in preceding for pattern in auth_patterns)
    
    def _extract_tags(self, file_path: str, path: str, bp_prefix: Optional[str]) -> List[str]:
        """Extract tags from context."""
        tags = []
        
        # From blueprint prefix
        if bp_prefix:
            tag = bp_prefix.strip('/').split('/')[0]
            if tag:
                tags.append(tag.title())
        
        # From file name
        if file_path:
            import os
            filename = os.path.basename(file_path).replace('.py', '')
            if filename not in ['__init__', 'routes', 'views', 'api']:
                tags.append(filename.title())
        
        # From path
        parts = path.strip('/').split('/')
        if parts and parts[0] and parts[0] not in [p.lower() for p in tags]:
            tags.append(parts[0].title())
        
        return tags[:2]  # Limit to 2 tags
