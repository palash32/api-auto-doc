"""AI-powered documentation generation service using Google Gemini."""

import google.generativeai as genai
from app.core.config import settings
from app.models.api_endpoint import APIEndpoint
import logging
import json

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            logger.warning("GEMINI_API_KEY not set - AI documentation will not be available")
            self.model = None

    async def generate_documentation(self, endpoint: APIEndpoint, code_snippet: str) -> dict:
        """Generate documentation for an API endpoint using Gemini AI."""
        if not self.model:
            logger.warning("AI model not initialized - returning empty documentation")
            return {
                "summary": "AI documentation unavailable",
                "description": "Please configure GEMINI_API_KEY to enable AI-powered documentation",
                "parameters": [],
                "responses": {}
            }

        prompt = f"""
        Analyze this API endpoint and generate comprehensive documentation.
        
        Endpoint: {endpoint.method} {endpoint.path}
        
        Code Context:
        {code_snippet}
        
        Output ONLY a JSON object with these keys:
        - "summary": Brief one-line description
        - "description": Detailed explanation of what this endpoint does
        - "parameters": Array of parameter objects with "name", "type", "required", "description"
        - "responses": Object with status codes as keys and descriptions as values
        
        Do not include markdown formatting, code blocks, or explanations outside the JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Parse JSON
            doc_data = json.loads(text)
            return doc_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response text: {response.text}")
            return {
                "summary": "Documentation generation failed",
                "description": f"AI returned invalid JSON: {str(e)}",
                "parameters": [],
                "responses": {}
            }
        except Exception as e:
            logger.error(f"Error generating docs: {e}")
            return {
                "summary": "Error generating documentation",
                "description": str(e),
                "parameters": [],
                "responses": {}
            }


# Global AI service instance
ai_service = AIService()
