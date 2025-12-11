"""AI Documentation Generator using Google Gemini API."""

import google.generativeai as genai
from typing import List, Dict, Optional
import asyncio
from functools import lru_cache
import hashlib

from app.core.config import settings


class GeminiDocGenerator:
    """
    AI-powered documentation generator using Google Gemini Pro.
    
    Generates comprehensive API documentation from code context using
    Google's Gemini model with caching for efficiency.
    """
    
    def __init__(self):
        """Initialize Gemini API client."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Generation configuration
        self.generation_config = {
            "temperature": settings.GEMINI_TEMPERATURE,
            "max_output_tokens": settings.GEMINI_MAX_TOKENS,
        }
    
    def _create_cache_key(self, *args) -> str:
        """Create cache key from arguments."""
        content = "|".join(str(arg) for arg in args)
        return hashlib.md5(content.encode()).hexdigest()
    
    async def generate_endpoint_description(
        self,
        code_context: str,
        endpoint_path: str,
        method: str,
        function_name: Optional[str] = None
    ) -> str:
        """
        Generate a comprehensive description for an API endpoint.
        
        Args:
            code_context: Source code of the endpoint function
            endpoint_path: API path (e.g., /api/users/{id})
            method: HTTP method (GET, POST, etc.)
            function_name: Name of the function/handler
            
        Returns:
            AI-generated description of the endpoint
        """
        prompt = f"""You are an expert technical writer creating API documentation.

Analyze this API endpoint and generate a clear, concise description:

**Endpoint:** {method} {endpoint_path}
**Function:** {function_name or 'N/A'}

**Code:**
```
{code_context}
```

Generate a 2-3 sentence description that explains:
1. What this endpoint does
2. What it returns or accomplishes
3. Any important behavior or side effects

Be concise, professional, and developer-friendly. Focus on the "what" and "why", not implementation details.
"""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=self.generation_config
            )
            return response.text.strip()
        except Exception as e:
            # Fallback description if AI fails
            return f"Endpoint for {method} {endpoint_path}"
    
    async def generate_parameter_docs(
        self,
        parameters: List[Dict],
        code_context: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate documentation for API parameters.
        
        Args:
            parameters: List of parameter dictionaries with name and type
            code_context: Optional code context for better understanding
            
        Returns:
            Enhanced parameters with AI-generated descriptions
        """
        if not parameters:
            return []
        
        param_str = "\n".join([
            f"- {p.get('name')} ({p.get('type', 'unknown')})"
            for p in parameters
        ])
        
        prompt = f"""Generate concise descriptions for these API parameters:

{param_str}

{f"Code context:\n```\n{code_context}\n```" if code_context else ""}

For each parameter, provide a ONE-LINE description that explains its purpose.
Format as JSON array: [{{"name": "param1", "description": "..."}}, ...]
"""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse response and merge with original parameters
            # Note: In production, you'd want robust JSON parsing here
            import json
            try:
                ai_params = json.loads(response.text.strip())
                for param in parameters:
                    ai_param = next(
                        (p for p in ai_params if p.get("name") == param.get("name")),
                        None
                    )
                    if ai_param:
                        param["description"] = ai_param.get("description", "")
            except json.JSONDecodeError:
                # If AI doesn't return valid JSON, skip enhancement
                pass
                
            return parameters
            
        except Exception:
            return parameters
    
    async def generate_example_requests(
        self,
        endpoint_path: str,
        method: str,
        parameters: Optional[List[Dict]] = None,
        request_body: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate example API requests in multiple formats.
        
        Args:
            endpoint_path: API path
            method: HTTP method
            parameters: Query/path parameters
            request_body: Request body schema
            
        Returns:
            Dictionary with example requests (curl, python, javascript)
        """
        prompt = f"""Generate example API requests for this endpoint:

**Endpoint:** {method} {endpoint_path}
**Parameters:** {parameters if parameters else 'None'}
**Request Body:** {request_body if request_body else 'None'}

Generate examples in these formats:
1. curl command
2. Python (using requests library)
3. JavaScript (using fetch)

Use realistic example values. For IDs use "123", for names use "John Doe", etc.
Format as JSON: {{"curl": "...", "python": "...", "javascript": "..."}}
"""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=self.generation_config
            )
            
            import json
            examples = json.loads(response.text.strip())
            return examples
            
        except Exception:
            # Fallback examples
            base_url = "https://api.example.com"
            url = f"{base_url}{endpoint_path}"
            
            return {
                "curl": f'curl -X {method} "{url}"',
                "python": f'import requests\nresponse = requests.{method.lower()}("{url}")',
                "javascript": f'fetch("{url}", {{ method: "{method}" }})'
            }
    
    async def infer_authentication_requirements(
        self,
        code_context: str
    ) -> Dict[str, any]:
        """
        Infer authentication requirements from code.
        
        Args:
            code_context: Source code to analyze
            
        Returns:
            Dictionary with authentication info
        """
        prompt = f"""Analyze this code and determine authentication requirements:

```
{code_context}
```

Look for decorators, middleware, or security checks that indicate:
- Is authentication required? (yes/no)
- What type? (Bearer token, API key, Basic auth, OAuth, etc.)
- Any specific permissions or roles needed?

Respond with JSON: {{"required": true/false, "type": "...", "notes": "..."}}
"""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=self.generation_config
            )
            
            import json
            auth_info = json.loads(response.text.strip())
            return auth_info
            
        except Exception:
            return {
                "required": False,
                "type": "unknown",
                "notes": "Could not determine from code"
            }
    
    async def suggest_best_practices(
        self,
        endpoint_path: str,
        method: str,
        code_context: str
    ) -> List[str]:
        """
        Suggest API best practices and potential improvements.
        
        Args:
            endpoint_path: API path
            method: HTTP method
            code_context: Source code
            
        Returns:
            List of best practice suggestions
        """
        prompt = f"""Review this API endpoint for best practices:

**Endpoint:** {method} {endpoint_path}

**Code:**
```
{code_context}
```

Provide 3-5 brief suggestions for:
- Security improvements
- Error handling
- Input validation
- Performance optimizations
- RESTful design

Format as a JSON array of strings: ["suggestion 1", "suggestion 2", ...]
"""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=self.generation_config
            )
            
            import json
            suggestions = json.loads(response.text.strip())
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception:
            return [
                "Add input validation for all parameters",
                "Implement proper error handling with specific status codes",
                "Add authentication if handling sensitive data",
                "Include rate limiting to prevent abuse",
                "Document expected response formats"
            ]


# Global instance
_doc_generator: Optional[GeminiDocGenerator] = None


def get_doc_generator() -> GeminiDocGenerator:
    """Get or create the global documentation generator instance."""
    global _doc_generator
    if _doc_generator is None:
        _doc_generator = GeminiDocGenerator()
    return _doc_generator
