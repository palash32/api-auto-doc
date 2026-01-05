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


SYSTEM_PROMPT = """You are an API documentation generator. You MUST return ONLY valid JSON.

CRITICAL: Your response must be PURE JSON with NO extra text before or after.
DO NOT wrap in markdown code blocks.
DO NOT add explanations.
DO NOT use newlines inside string values.

Return this exact JSON structure:
{
  "summary": "one-line description here",
  "description": "detailed multi-line description here",
  "parameters": [],
  "request_body": null,
  "responses": [{"status": 200, "description": "Success"}],
  "tags": [],
  "auth_required": false
}

Replace the placeholder text with actual documentation. Keep all strings on single lines (no embedded newlines)."""


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
        
        # Try to extract JSON if embedded in text
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        # Parse response with better error handling
        try:
            documentation = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to fix common issues
            logger.warning("First JSON parse failed, attempting fixes...")
            logger.error(f"Raw response that failed: {content[:500]}")
            
            # Create minimal fallback documentation
            documentation = {
                "summary": f"{endpoint.method} {endpoint.path}",
                "description": "Documentation generation failed. Please edit manually.",
                "parameters": [],
                "request_body": None,
                "responses": [{"status": 200, "description": "Success"}],
                "tags": [],
                "auth_required": False
            }
            logger.warning("Using fallback documentation due to parse error")
        
        logger.info(f"Generated docs for {endpoint.method} {endpoint.path} via Gemini")
        
        return DocumentationResult(
            documentation=documentation,
            input_tokens=0,  # Gemini doesn't expose token counts easily
            output_tokens=0,
            cost=0.0  # Free tier
        )
        
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise

