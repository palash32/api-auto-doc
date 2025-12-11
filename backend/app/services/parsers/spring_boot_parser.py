"""Spring Boot (Java) API endpoint parser."""

import re
from typing import List, Optional
from app.services.parsers.base_parser import BaseParser, ParsedEndpoint, ParsedParameter


class SpringBootParser(BaseParser):
    """
    Parser for Spring Boot REST API endpoints.
    
    Detects patterns like:
    - @GetMapping("/path")
    - @PostMapping("/path")
    - @RequestMapping(value="/path", method=RequestMethod.GET)
    - @RestController with @RequestMapping class-level prefix
    """
    
    FRAMEWORK_NAME = "spring_boot"
    SUPPORTED_EXTENSIONS = [".java", ".kt"]  # Java and Kotlin
    FRAMEWORK_INDICATORS = [
        "@RestController",
        "@Controller",
        "@RequestMapping",
        "@GetMapping",
        "@PostMapping",
        "@PutMapping",
        "@DeleteMapping",
        "@PatchMapping",
        "org.springframework.web",
        "import org.springframework"
    ]
    
    # Specific method mapping annotations
    METHOD_MAPPINGS = {
        'GetMapping': 'GET',
        'PostMapping': 'POST',
        'PutMapping': 'PUT',
        'DeleteMapping': 'DELETE',
        'PatchMapping': 'PATCH'
    }
    
    # Method mapping pattern
    METHOD_ANNOTATION = re.compile(
        r'@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:value\s*=\s*)?[\'"]?([^\'")\s]+)[\'"]?\s*\)',
        re.MULTILINE
    )
    
    # Simple method mapping without path
    SIMPLE_METHOD_ANNOTATION = re.compile(
        r'@(Get|Post|Put|Delete|Patch)Mapping\s*(?:\(\s*\))?\s*\n',
        re.MULTILINE
    )
    
    # Generic RequestMapping
    REQUEST_MAPPING = re.compile(
        r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?[\'"]?([^\'")\s,]+)[\'"]?(?:\s*,\s*method\s*=\s*RequestMethod\.(\w+))?\s*\)',
        re.MULTILINE
    )
    
    # Class-level RequestMapping for base path
    CLASS_MAPPING = re.compile(
        r'@RequestMapping\s*\(\s*[\'"]?([^\'")\s]+)[\'"]?\s*\)\s*\n\s*public\s+class',
        re.MULTILINE
    )
    
    # Controller class pattern
    CONTROLLER_CLASS = re.compile(
        r'@(?:Rest)?Controller\s*(?:\([^)]*\))?\s*\n(?:@RequestMapping\s*\(\s*[\'"]?([^\'")\s]+)[\'"]?\s*\)\s*\n)?\s*public\s+class\s+(\w+)',
        re.MULTILINE | re.DOTALL
    )
    
    # Method definition
    METHOD_DEF = re.compile(
        r'public\s+(?:\w+\s+)?(\w+)\s*\(',
        re.MULTILINE
    )
    
    # PathVariable annotation
    PATH_VARIABLE = re.compile(
        r'@PathVariable(?:\s*\([^)]*\))?\s+\w+\s+(\w+)',
        re.MULTILINE
    )
    
    # RequestParam annotation
    REQUEST_PARAM = re.compile(
        r'@RequestParam(?:\s*\(\s*(?:value\s*=\s*)?[\'"]?(\w+)[\'"]?)?(?:\s*,\s*required\s*=\s*(true|false))?\s*\)?\s+\w+\s+(\w+)',
        re.MULTILINE
    )
    
    def parse_file(self, file_path: str) -> List[ParsedEndpoint]:
        """Parse a Spring Boot file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_content(content, file_path)
        except Exception as e:
            return []
    
    def parse_content(self, content: str, file_path: str = "") -> List[ParsedEndpoint]:
        """Parse Spring Boot content for API endpoints."""
        endpoints = []
        
        # Find class-level base path
        base_path = ""
        controller_match = self.CONTROLLER_CLASS.search(content)
        if controller_match:
            base_path = controller_match.group(1) or ""
            class_name = controller_match.group(2)
        else:
            class_name = "Controller"
        
        # Parse specific method mappings (@GetMapping, etc.)
        for match in self.METHOD_ANNOTATION.finditer(content):
            method_type = match.group(1) + "Mapping"
            path = match.group(2)
            
            http_method = self.METHOD_MAPPINGS.get(method_type, 'GET')
            full_path = self.normalize_path(base_path + path)
            line_number = content[:match.start()].count('\n') + 1
            
            # Find method name
            func_name = self._find_method_name(content, match.end())
            
            # Extract parameters
            parameters = self._extract_parameters(content, match.end())
            
            endpoint = ParsedEndpoint(
                path=full_path,
                method=http_method,
                function_name=f"{class_name}.{func_name}" if func_name else class_name,
                file_path=file_path,
                line_number=line_number,
                parameters=parameters,
                tags=[class_name.replace('Controller', '')]
            )
            endpoints.append(endpoint)
        
        # Parse simple method mappings without explicit path
        for match in self.SIMPLE_METHOD_ANNOTATION.finditer(content):
            method_type = match.group(1) + "Mapping"
            http_method = self.METHOD_MAPPINGS.get(method_type, 'GET')
            line_number = content[:match.start()].count('\n') + 1
            
            func_name = self._find_method_name(content, match.end())
            full_path = self.normalize_path(base_path) if base_path else "/"
            
            endpoint = ParsedEndpoint(
                path=full_path,
                method=http_method,
                function_name=f"{class_name}.{func_name}" if func_name else class_name,
                file_path=file_path,
                line_number=line_number,
                tags=[class_name.replace('Controller', '')]
            )
            endpoints.append(endpoint)
        
        # Parse @RequestMapping with method specification
        for match in self.REQUEST_MAPPING.finditer(content):
            path = match.group(1)
            method = match.group(2) or 'GET'
            
            # Skip class-level mappings
            if 'public class' in content[match.end():match.end() + 50]:
                continue
            
            full_path = self.normalize_path(base_path + path)
            line_number = content[:match.start()].count('\n') + 1
            func_name = self._find_method_name(content, match.end())
            
            endpoint = ParsedEndpoint(
                path=full_path,
                method=method.upper(),
                function_name=f"{class_name}.{func_name}" if func_name else class_name,
                file_path=file_path,
                line_number=line_number,
                tags=[class_name.replace('Controller', '')]
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _find_method_name(self, content: str, start_pos: int) -> str:
        """Find the method name after an annotation."""
        search_area = content[start_pos:start_pos + 300]
        match = self.METHOD_DEF.search(search_area)
        
        if match:
            return match.group(1)
        return ""
    
    def _extract_parameters(self, content: str, start_pos: int) -> List[ParsedParameter]:
        """Extract parameters from method signature."""
        parameters = []
        search_area = content[start_pos:start_pos + 500]
        
        # Find method signature
        method_match = re.search(r'public\s+\w+\s+\w+\s*\(([^)]+)\)', search_area)
        if not method_match:
            return parameters
        
        signature = method_match.group(1)
        
        # @PathVariable parameters
        for match in self.PATH_VARIABLE.finditer(signature):
            param_name = match.group(1)
            parameters.append(ParsedParameter(
                name=param_name,
                param_type="path",
                required=True
            ))
        
        # @RequestParam parameters
        for match in self.REQUEST_PARAM.finditer(signature):
            param_name = match.group(1) or match.group(3)
            required = match.group(2) != 'false' if match.group(2) else True
            parameters.append(ParsedParameter(
                name=param_name,
                param_type="query",
                required=required
            ))
        
        return parameters
