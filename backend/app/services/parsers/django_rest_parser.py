"""Django REST Framework API endpoint parser."""

import re
from typing import List, Optional, Tuple
from app.services.parsers.base_parser import BaseParser, ParsedEndpoint, ParsedParameter


class DjangoRESTParser(BaseParser):
    """
    Parser for Django REST Framework API endpoints.
    
    Detects patterns like:
    - @api_view(['GET'])
    - class MyViewSet(ViewSet)
    - path('users/', UserViewSet.as_view())
    - router.register('users', UserViewSet)
    """
    
    FRAMEWORK_NAME = "django_rest"
    SUPPORTED_EXTENSIONS = [".py"]
    FRAMEWORK_INDICATORS = [
        "from rest_framework",
        "rest_framework.views",
        "rest_framework.viewsets",
        "rest_framework.decorators",
        "@api_view",
        "APIView",
        "ViewSet",
        "ModelViewSet"
    ]
    
    # @api_view decorator pattern
    API_VIEW_DECORATOR = re.compile(
        r'@api_view\s*\(\s*\[([^\]]+)\]\s*\)',
        re.MULTILINE
    )
    
    # Class-based view patterns
    CLASS_VIEW = re.compile(
        r'class\s+(\w+)\s*\(\s*(?:[\w.]+\s*,\s*)*(\w*(?:APIView|ViewSet|ModelViewSet|GenericAPIView))',
        re.MULTILINE
    )
    
    # URL patterns
    URL_PATH = re.compile(
        r'path\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(\w+)(?:\.as_view\(\))?',
        re.MULTILINE
    )
    
    # Router register pattern
    ROUTER_REGISTER = re.compile(
        r'router\s*\.\s*register\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(\w+)',
        re.MULTILINE
    )
    
    # Method definitions in class
    METHOD_DEF = re.compile(
        r'def\s+(get|post|put|patch|delete|list|create|retrieve|update|partial_update|destroy)\s*\(',
        re.MULTILINE | re.IGNORECASE
    )
    
    # ViewSet action to HTTP method mapping
    VIEWSET_ACTIONS = {
        'list': 'GET',
        'create': 'POST',
        'retrieve': 'GET',
        'update': 'PUT',
        'partial_update': 'PATCH',
        'destroy': 'DELETE'
    }
    
    def parse_file(self, file_path: str) -> List[ParsedEndpoint]:
        """Parse a Django REST Framework file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_content(content, file_path)
        except Exception as e:
            return []
    
    def parse_content(self, content: str, file_path: str = "") -> List[ParsedEndpoint]:
        """Parse Django REST Framework content for API endpoints."""
        endpoints = []
        
        # Parse function-based views with @api_view
        endpoints.extend(self._parse_api_view_functions(content, file_path))
        
        # Parse class-based views
        endpoints.extend(self._parse_class_views(content, file_path))
        
        return endpoints
    
    def _parse_api_view_functions(self, content: str, file_path: str) -> List[ParsedEndpoint]:
        """Parse @api_view decorated functions."""
        endpoints = []
        
        for match in self.API_VIEW_DECORATOR.finditer(content):
            methods_str = match.group(1)
            methods = re.findall(r'[\'"](\w+)[\'"]', methods_str)
            
            # Find function name
            func_match = re.search(r'def\s+(\w+)\s*\(', content[match.end():match.end() + 200])
            if not func_match:
                continue
            
            func_name = func_match.group(1)
            line_number = content[:match.start()].count('\n') + 1
            
            # Infer path from function name
            path = "/" + func_name.replace('_', '-')
            
            # Extract docstring
            func_start = match.end() + func_match.end()
            description = self._extract_docstring(content, func_start)
            
            for method in methods:
                endpoint = ParsedEndpoint(
                    path=path,
                    method=method.upper(),
                    function_name=func_name,
                    file_path=file_path,
                    line_number=line_number,
                    description=description,
                    tags=["API"]
                )
                endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_class_views(self, content: str, file_path: str) -> List[ParsedEndpoint]:
        """Parse class-based APIViews and ViewSets."""
        endpoints = []
        
        for match in self.CLASS_VIEW.finditer(content):
            class_name = match.group(1)
            base_class = match.group(2)
            line_number = content[:match.start()].count('\n') + 1
            
            # Find class body
            class_start = match.end()
            class_body = self._extract_class_body(content, class_start)
            
            # Infer base path from class name
            base_path = "/" + self._class_to_path(class_name)
            
            # Find methods in class
            for method_match in self.METHOD_DEF.finditer(class_body):
                method_name = method_match.group(1).lower()
                
                # Map ViewSet actions to HTTP methods
                if method_name in self.VIEWSET_ACTIONS:
                    http_method = self.VIEWSET_ACTIONS[method_name]
                    path = base_path
                    
                    # Retrieve, update, destroy need {id}
                    if method_name in ['retrieve', 'update', 'partial_update', 'destroy']:
                        path = f"{base_path}/{{id}}"
                else:
                    http_method = method_name.upper()
                    path = base_path
                
                func_line = content[:class_start].count('\n') + class_body[:method_match.start()].count('\n') + 1
                
                endpoint = ParsedEndpoint(
                    path=path,
                    method=http_method,
                    function_name=f"{class_name}.{method_name}",
                    file_path=file_path,
                    line_number=func_line,
                    tags=[class_name.replace('ViewSet', '').replace('View', '')]
                )
                endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_class_body(self, content: str, start_pos: int) -> str:
        """Extract class body content."""
        # Find next class or end of file
        remaining = content[start_pos:]
        next_class = re.search(r'\nclass\s+\w+', remaining)
        
        if next_class:
            return remaining[:next_class.start()]
        return remaining[:2000]  # Limit to avoid huge searches
    
    def _extract_docstring(self, content: str, start_pos: int) -> str:
        """Extract docstring after function definition."""
        search_area = content[start_pos:start_pos + 500]
        match = re.search(r'"""(.*?)"""', search_area, re.DOTALL)
        
        if match:
            return match.group(1).strip().split('\n')[0]
        return ""
    
    def _class_to_path(self, class_name: str) -> str:
        """Convert class name to URL path."""
        # UserViewSet -> users
        # ArticleAPIView -> articles
        name = class_name.replace('ViewSet', '').replace('APIView', '').replace('View', '')
        
        # CamelCase to snake_case
        path = re.sub(r'([A-Z])', r'-\1', name).lower().strip('-')
        
        # Pluralize (simple)
        if not path.endswith('s'):
            path += 's'
        
        return path
