import json
import logging
import google.generativeai as genai
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Service for interacting with Google Gemini API.
    """
    
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. AI features will be disabled.")
            self.model = None
            return
            
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
    async def generate_documentation(self, code_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate documentation for a given code snippet metadata.
        
        Args:
            code_metadata: Dict containing function name, params, docstring, etc.
            
        Returns:
            Dict containing summary, description, tags, etc.
        """
        if not self.model:
            return {"error": "AI service not configured"}
            
        prompt = self._build_prompt(code_metadata)
        
        try:
            # Generate response
            response = await self.model.generate_content_async(prompt)
            text = response.text
            
            # Parse JSON
            return self._parse_json_response(text)
            
        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            return {"error": str(e)}
            
    def _build_prompt(self, metadata: Dict[str, Any]) -> str:
        """
        Construct a strict prompt for Gemini.
        """
        return f"""
        You are an expert API documenter. Your task is to analyze the following Python function metadata and generate structured API documentation in JSON format.
        
        METADATA:
        {json.dumps(metadata, indent=2)}
        
        INSTRUCTIONS:
        1. Analyze the function name, parameters, docstring, and decorators.
        2. Infer the HTTP method (GET, POST, etc.) if possible from decorators (e.g., @app.get). Default to "GET" if unknown.
        3. Generate a concise summary (1 sentence).
        4. Generate a detailed description (2-3 sentences).
        5. Suggest 3-5 relevant tags.
        6. Identify if authentication is likely required (based on names like 'user', 'auth', 'token' or decorators).
        
        OUTPUT FORMAT:
        You must return ONLY a valid JSON object. Do not include markdown formatting (```json ... ```).
        
        {{
            "summary": "Brief summary of what the endpoint does",
            "description": "Detailed explanation including purpose and side effects",
            "method": "HTTP_METHOD",
            "tags": ["tag1", "tag2"],
            "auth_required": true/false,
            "auth_type": "Bearer/API Key/None"
        }}
        """

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        Clean and parse JSON response from LLM.
        """
        try:
            # Remove markdown code blocks if present
            cleaned_text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Gemini: {text}")
            return {
                "summary": "Failed to generate documentation",
                "description": "AI response was not valid JSON.",
                "tags": ["error"]
            }

    async def generate_doc(self, code_content: str, language: str) -> Optional[Dict[str, Any]]:
        """
        Generate documentation for code content by analyzing it for API endpoints.
        
        Args:
            code_content: The source code to analyze
            language: Programming language (python, javascript, typescript, etc.)
            
        Returns:
            Dict with API endpoint documentation if found, None otherwise
        """
        if not self.model:
            logger.warning("AI model not configured, skipping doc generation")
            return None
            
        # Build a prompt to identify and document API endpoints
        prompt = f"""
You are an expert API documentation generator. Analyze the following {language} code and identify if it contains an API endpoint.

CODE:
```{language}
{code_content[:3000]}
```

TASK:
1. Determine if this code defines an API endpoint (e.g., FastAPI route, Express route, Flask route, Spring controller, etc.)
2. If it IS an API endpoint, extract the following information:
   - HTTP method (GET, POST, PUT, DELETE, PATCH)
   - Path/route
   - Summary (brief description)
   - Description (detailed explanation)
   - Tags (relevant categories)
   - Whether authentication is required
   - Parameters and request body if identifiable

3. If it is NOT an API endpoint, return exactly: {{"is_api": false}}

OUTPUT FORMAT (return ONLY valid JSON, no markdown):
For API endpoints:
{{
    "is_api": true,
    "path": "/api/example",
    "method": "GET",
    "summary": "Brief summary",
    "description": "Detailed description",
    "tags": ["tag1", "tag2"],
    "auth_required": false,
    "auth_type": null,
    "parameters": [],
    "request_body": {{}},
    "responses": []
}}

For non-API code:
{{"is_api": false}}
"""
        try:
            response = await self.model.generate_content_async(prompt)
            result = self._parse_json_response(response.text)
            
            # Return None if not an API endpoint
            if not result.get("is_api", False):
                return None
                
            # Remove is_api flag from output
            result.pop("is_api", None)
            return result
            
        except Exception as e:
            logger.error(f"Error generating doc: {e}")
            return None

