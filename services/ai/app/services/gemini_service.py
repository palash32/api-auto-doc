"""
Google Gemini AI Integration Service
"""

import logging
from dataclasses import dataclass
from typing import Optional
import json
import re

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Gemini client
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


@dataclass
class DocumentationResult:
    """Result of documentation generation."""
    documentation: dict
    input_tokens: int
    output_tokens: int
    cost: float  # Always 0 for free tier


SYSTEM_PROMPT = """You are an expert API documentation writer. Given code for an API endpoint, generate comprehensive documentation.

Return ONLY a valid JSON object (no markdown, no code blocks) with:
{
  "summary": "Brief one-line description",
  "description": "Detailed description of what this endpoint does",
  "parameters": [
    {"name": "param_name", "in": "path|query|header", "type": "string|integer|boolean", "required": true, "description": "..."}
  ],
  "request_body": {"type": "object", "properties": {}} or null if no body,
  "responses": [
    {"status": 200, "description": "Success response description"}
  ],
  "tags": ["category"],
  "auth_required": false
}

Be concise. Return only the JSON, nothing else."""


async def generate_documentation(endpoint) -> DocumentationResult:
    """
    Generate documentation for an endpoint using Google Gemini.
    
    Args:
        endpoint: EndpointInput with path, method, code_snippet
        
    Returns:
        DocumentationResult with generated docs
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("Gemini API key not configured")
    
    user_prompt = f"""Generate API documentation for this endpoint:

Method: {endpoint.method}
Path: {endpoint.path}
Language: {endpoint.language or 'unknown'}
File: {endpoint.file_path or 'unknown'}

Code:
{endpoint.code_snippet}

Return only valid JSON, no markdown code blocks."""

    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\n{user_prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1000,
            )
        )
        
        # Extract text
        content = response.text
        
        # Remove markdown code blocks if present
        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE)
        content = content.strip()
        
        # Parse response
        documentation = json.loads(content)
        
        logger.info(f"Generated docs for {endpoint.method} {endpoint.path} via Gemini")
        
        return DocumentationResult(
            documentation=documentation,
            input_tokens=0,  # Gemini doesn't expose token counts easily
            output_tokens=0,
            cost=0.0  # Free tier
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.error(f"Raw response: {content[:500]}")
        raise ValueError(f"Invalid JSON response from Gemini: {e}")
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise
