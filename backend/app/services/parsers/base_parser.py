"""Base parser class and interface for framework-specific API endpoint detection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class HTTPMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class ParsedParameter:
    """Represents a parsed API parameter."""
    name: str
    param_type: str = "query"  # path, query, header, body
    data_type: str = "string"
    required: bool = False
    description: str = ""
    default: Optional[Any] = None


@dataclass
class ParsedEndpoint:
    """Represents a parsed API endpoint."""
    path: str
    method: str
    function_name: str
    file_path: str
    line_number: int
    
    # Optional metadata
    summary: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[ParsedParameter] = field(default_factory=list)
    request_body_type: Optional[str] = None
    response_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    auth_required: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            "path": self.path,
            "method": self.method,
            "function_name": self.function_name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.param_type,
                    "data_type": p.data_type,
                    "required": p.required,
                    "description": p.description
                }
                for p in self.parameters
            ],
            "request_body_type": self.request_body_type,
            "response_type": self.response_type,
            "auth_required": self.auth_required
        }


class BaseParser(ABC):
    """
    Abstract base class for framework-specific parsers.
    
    Each framework parser should inherit from this and implement
    the parse_file and parse_content methods.
    """
    
    # Framework name for identification
    FRAMEWORK_NAME: str = "unknown"
    
    # File extensions this parser handles
    SUPPORTED_EXTENSIONS: List[str] = []
    
    # Patterns that indicate this framework is used
    FRAMEWORK_INDICATORS: List[str] = []
    
    @abstractmethod
    def parse_file(self, file_path: str) -> List[ParsedEndpoint]:
        """
        Parse a file and extract API endpoints.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            List of ParsedEndpoint objects
        """
        pass
    
    @abstractmethod
    def parse_content(self, content: str, file_path: str = "") -> List[ParsedEndpoint]:
        """
        Parse file content and extract API endpoints.
        
        Args:
            content: File content as string
            file_path: Optional file path for reference
            
        Returns:
            List of ParsedEndpoint objects
        """
        pass
    
    def detect_framework(self, content: str) -> bool:
        """
        Check if the content uses this framework.
        
        Args:
            content: File content to check
            
        Returns:
            True if framework indicators are found
        """
        for indicator in self.FRAMEWORK_INDICATORS:
            if indicator in content:
                return True
        return False
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize API path (ensure leading slash, no trailing slash)."""
        if not path.startswith("/"):
            path = "/" + path
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return path
    
    @staticmethod
    def extract_path_params(path: str) -> List[str]:
        """
        Extract path parameters from a route path.
        
        Examples:
            /users/:id -> ["id"]
            /users/{id}/posts/{post_id} -> ["id", "post_id"]
            /users/<int:user_id> -> ["user_id"]
        """
        import re
        params = []
        
        # Express.js style: :param
        params.extend(re.findall(r':(\w+)', path))
        
        # OpenAPI/FastAPI style: {param}
        params.extend(re.findall(r'\{(\w+)\}', path))
        
        # Flask style: <type:param> or <param>
        params.extend(re.findall(r'<(?:\w+:)?(\w+)>', path))
        
        return list(set(params))


class ParserRegistry:
    """Registry for framework parsers."""
    
    _parsers: Dict[str, BaseParser] = {}
    
    @classmethod
    def register(cls, parser: BaseParser):
        """Register a parser."""
        cls._parsers[parser.FRAMEWORK_NAME] = parser
    
    @classmethod
    def get_parser(cls, framework_name: str) -> Optional[BaseParser]:
        """Get a parser by framework name."""
        return cls._parsers.get(framework_name)
    
    @classmethod
    def get_all_parsers(cls) -> List[BaseParser]:
        """Get all registered parsers."""
        return list(cls._parsers.values())
    
    @classmethod
    def detect_framework(cls, content: str, file_ext: str) -> Optional[BaseParser]:
        """
        Auto-detect which framework a file uses.
        
        Args:
            content: File content
            file_ext: File extension (e.g., ".py", ".js")
            
        Returns:
            Matching parser or None
        """
        for parser in cls._parsers.values():
            if file_ext in parser.SUPPORTED_EXTENSIONS:
                if parser.detect_framework(content):
                    return parser
        return None
