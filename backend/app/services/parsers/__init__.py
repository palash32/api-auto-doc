"""
Multi-framework parser package.

Provides parsers for detecting and extracting API endpoints from various frameworks:
- Express.js (Node.js)
- Flask (Python)
- Django REST Framework (Python)
- FastAPI (Python) - native support
- Spring Boot (Java)
- Go Gin/Echo (Go)
"""

from app.services.parsers.base_parser import (
    BaseParser,
    ParsedEndpoint,
    ParsedParameter,
    ParserRegistry,
    HTTPMethod
)
from app.services.parsers.express_parser import ExpressParser
from app.services.parsers.flask_parser import FlaskParser
from app.services.parsers.django_rest_parser import DjangoRESTParser
from app.services.parsers.spring_boot_parser import SpringBootParser
from app.services.parsers.go_gin_parser import GoGinParser


# Register all parsers
ParserRegistry.register(ExpressParser())
ParserRegistry.register(FlaskParser())
ParserRegistry.register(DjangoRESTParser())
ParserRegistry.register(SpringBootParser())
ParserRegistry.register(GoGinParser())


def get_parser_for_file(file_path: str, content: str = None) -> BaseParser | None:
    """
    Get the appropriate parser for a file.
    
    Args:
        file_path: Path to the file
        content: Optional file content (will be read if not provided)
    
    Returns:
        Matching parser or None
    """
    import os
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if content is None:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None
    
    return ParserRegistry.detect_framework(content, ext)


def parse_file(file_path: str) -> list[ParsedEndpoint]:
    """
    Parse a file and extract API endpoints.
    
    Automatically detects the framework and uses the appropriate parser.
    
    Args:
        file_path: Path to the file to parse
        
    Returns:
        List of ParsedEndpoint objects
    """
    parser = get_parser_for_file(file_path)
    
    if parser:
        return parser.parse_file(file_path)
    
    return []


def parse_directory(directory_path: str, recursive: bool = True) -> list[ParsedEndpoint]:
    """
    Parse all files in a directory for API endpoints.
    
    Args:
        directory_path: Path to the directory
        recursive: Whether to search subdirectories
        
    Returns:
        List of all ParsedEndpoint objects found
    """
    import os
    
    all_endpoints = []
    supported_exts = {'.py', '.js', '.ts', '.java', '.go', '.kt', '.mjs'}
    
    if recursive:
        for root, dirs, files in os.walk(directory_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in {
                'node_modules', '.git', '__pycache__', 'venv', '.venv',
                'target', 'build', 'dist', 'vendor'
            }]
            
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in supported_exts:
                    file_path = os.path.join(root, filename)
                    endpoints = parse_file(file_path)
                    all_endpoints.extend(endpoints)
    else:
        for filename in os.listdir(directory_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in supported_exts:
                file_path = os.path.join(directory_path, filename)
                endpoints = parse_file(file_path)
                all_endpoints.extend(endpoints)
    
    return all_endpoints


__all__ = [
    'BaseParser',
    'ParsedEndpoint',
    'ParsedParameter',
    'ParserRegistry',
    'HTTPMethod',
    'ExpressParser',
    'FlaskParser',
    'DjangoRESTParser',
    'SpringBootParser',
    'GoGinParser',
    'get_parser_for_file',
    'parse_file',
    'parse_directory'
]
