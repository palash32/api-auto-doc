"""Advanced AI service for enhanced documentation generation."""

import json
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from app.core.config import settings
from app.core.logger import logger

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-generativeai not installed, AI features disabled")


@dataclass
class EnhancedDescription:
    """Result of AI-enhanced description generation."""
    original: str
    enhanced: str
    summary: str  # One-line summary
    improvements: List[str]  # What was improved


@dataclass
class GeneratedExample:
    """Generated code example for an endpoint."""
    language: str
    code: str
    description: str


@dataclass
class TypeInference:
    """Inferred type information."""
    param_name: str
    inferred_type: str
    confidence: float  # 0-1
    reason: str


@dataclass
class BreakingChange:
    """Detected breaking change between versions."""
    change_type: str  # removed, type_changed, required_changed, etc.
    path: str
    field: Optional[str]
    old_value: Any
    new_value: Any
    severity: str  # high, medium, low
    description: str


@dataclass
class QualityScore:
    """API quality assessment."""
    overall_score: int  # 0-100
    categories: Dict[str, int]  # e.g., {"naming": 80, "consistency": 90}
    issues: List[str]
    suggestions: List[str]


class AdvancedAIService:
    """
    Advanced AI service for documentation enhancement.
    
    Features:
    - Enhance brief descriptions
    - Generate code examples
    - Infer types from code
    - Detect breaking changes
    - Score API quality
    """
    
    def __init__(self):
        self.model = None
        if GENAI_AVAILABLE and settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("Advanced AI service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AI model: {e}")
    
    async def enhance_description(
        self,
        original_description: str,
        endpoint_context: Dict[str, Any]
    ) -> EnhancedDescription:
        """
        Enhance a brief or unclear API description using AI.
        
        Args:
            original_description: The original description to enhance
            endpoint_context: Context about the endpoint (method, path, params, etc.)
        
        Returns:
            EnhancedDescription with improved text
        """
        if not self.model:
            return EnhancedDescription(
                original=original_description,
                enhanced=original_description,
                summary=original_description[:100],
                improvements=[]
            )
        
        prompt = f"""You are an API documentation expert. Enhance this API endpoint description to be clearer and more comprehensive.

Endpoint: {endpoint_context.get('method', 'GET')} {endpoint_context.get('path', '')}
Current Description: {original_description or 'No description provided'}
Parameters: {json.dumps(endpoint_context.get('parameters', []))}

Requirements:
1. Keep technical accuracy
2. Be concise but complete (2-4 sentences)
3. Mention key parameters if relevant
4. Use active voice
5. Start with a verb (Returns, Creates, Updates, etc.)

Respond in JSON format:
{{
  "enhanced": "Improved description text",
  "summary": "One-line summary under 80 chars",
  "improvements": ["List of what was improved"]
}}"""

        try:
            response = await self._generate(prompt)
            data = self._parse_json_response(response)
            
            return EnhancedDescription(
                original=original_description,
                enhanced=data.get("enhanced", original_description),
                summary=data.get("summary", original_description[:80]),
                improvements=data.get("improvements", [])
            )
        except Exception as e:
            logger.error(f"Description enhancement failed: {e}")
            return EnhancedDescription(
                original=original_description,
                enhanced=original_description,
                summary=original_description[:80] if original_description else "",
                improvements=[]
            )
    
    async def generate_examples(
        self,
        endpoint: Dict[str, Any],
        languages: List[str] = None
    ) -> List[GeneratedExample]:
        """
        Generate code examples for an endpoint in multiple languages.
        
        Args:
            endpoint: Endpoint information
            languages: Languages to generate (default: curl, python, javascript)
        
        Returns:
            List of GeneratedExample for each language
        """
        if languages is None:
            languages = ["curl", "python", "javascript"]
        
        if not self.model:
            # Return basic template examples
            return self._generate_template_examples(endpoint, languages)
        
        prompt = f"""Generate code examples for this API endpoint in the following languages: {', '.join(languages)}

Endpoint: {endpoint.get('method', 'GET')} {endpoint.get('path', '')}
Description: {endpoint.get('description', '')}
Parameters: {json.dumps(endpoint.get('parameters', []))}
Request Body: {json.dumps(endpoint.get('request_body', {}))}

Requirements:
1. Use realistic sample data
2. Include error handling where appropriate
3. Follow language best practices
4. Make examples copy-paste ready

Respond in JSON format:
{{
  "examples": [
    {{"language": "curl", "code": "...", "description": "Using cURL"}},
    {{"language": "python", "code": "...", "description": "Using Python requests"}},
    {{"language": "javascript", "code": "...", "description": "Using fetch API"}}
  ]
}}"""

        try:
            response = await self._generate(prompt)
            data = self._parse_json_response(response)
            
            return [
                GeneratedExample(
                    language=ex.get("language", "unknown"),
                    code=ex.get("code", ""),
                    description=ex.get("description", "")
                )
                for ex in data.get("examples", [])
            ]
        except Exception as e:
            logger.error(f"Example generation failed: {e}")
            return self._generate_template_examples(endpoint, languages)
    
    async def infer_types(
        self,
        code_snippet: str,
        language: str = "python"
    ) -> List[TypeInference]:
        """
        Infer parameter and return types from code.
        
        Args:
            code_snippet: Source code to analyze
            language: Programming language
        
        Returns:
            List of TypeInference for detected parameters
        """
        if not self.model:
            return []
        
        prompt = f"""Analyze this {language} code and infer types for all parameters and return values.

Code:
```{language}
{code_snippet}
```

For each parameter/variable, provide:
1. Name
2. Inferred type (be specific: str, int, List[dict], etc.)
3. Confidence (0-1)
4. Why you inferred this type

Respond in JSON format:
{{
  "inferences": [
    {{"name": "user_id", "type": "int", "confidence": 0.95, "reason": "Used as path parameter with numeric value"}},
    ...
  ]
}}"""

        try:
            response = await self._generate(prompt)
            data = self._parse_json_response(response)
            
            return [
                TypeInference(
                    param_name=inf.get("name", ""),
                    inferred_type=inf.get("type", "unknown"),
                    confidence=float(inf.get("confidence", 0.5)),
                    reason=inf.get("reason", "")
                )
                for inf in data.get("inferences", [])
            ]
        except Exception as e:
            logger.error(f"Type inference failed: {e}")
            return []
    
    async def detect_breaking_changes(
        self,
        old_spec: Dict[str, Any],
        new_spec: Dict[str, Any]
    ) -> List[BreakingChange]:
        """
        Detect breaking changes between two API versions.
        
        Args:
            old_spec: Previous API specification
            new_spec: New API specification
        
        Returns:
            List of BreakingChange detections
        """
        changes = []
        
        # Check removed endpoints
        old_paths = set(old_spec.get("paths", {}).keys())
        new_paths = set(new_spec.get("paths", {}).keys())
        
        for removed_path in old_paths - new_paths:
            changes.append(BreakingChange(
                change_type="endpoint_removed",
                path=removed_path,
                field=None,
                old_value=removed_path,
                new_value=None,
                severity="high",
                description=f"Endpoint {removed_path} was removed"
            ))
        
        # Check modified endpoints
        for path in old_paths & new_paths:
            old_endpoint = old_spec["paths"].get(path, {})
            new_endpoint = new_spec["paths"].get(path, {})
            
            # Check removed methods
            old_methods = set(old_endpoint.keys())
            new_methods = set(new_endpoint.keys())
            
            for removed_method in old_methods - new_methods:
                changes.append(BreakingChange(
                    change_type="method_removed",
                    path=path,
                    field=removed_method,
                    old_value=removed_method,
                    new_value=None,
                    severity="high",
                    description=f"{removed_method.upper()} method removed from {path}"
                ))
            
            # Check parameter changes
            for method in old_methods & new_methods:
                old_params = old_endpoint[method].get("parameters", [])
                new_params = new_endpoint[method].get("parameters", [])
                
                old_param_names = {p.get("name") for p in old_params}
                new_param_names = {p.get("name") for p in new_params}
                
                # Check for new required params
                for param in new_params:
                    if param.get("required") and param.get("name") not in old_param_names:
                        changes.append(BreakingChange(
                            change_type="required_param_added",
                            path=path,
                            field=param.get("name"),
                            old_value=None,
                            new_value=param,
                            severity="high",
                            description=f"New required parameter '{param.get('name')}' added to {method.upper()} {path}"
                        ))
        
        return changes
    
    async def score_api_quality(
        self,
        endpoints: List[Dict[str, Any]]
    ) -> QualityScore:
        """
        Generate an API quality score with suggestions.
        
        Args:
            endpoints: List of endpoint specifications
        
        Returns:
            QualityScore with overall score and suggestions
        """
        issues = []
        suggestions = []
        scores = {
            "naming": 100,
            "consistency": 100,
            "documentation": 100,
            "design": 100
        }
        
        # Check naming conventions
        for endpoint in endpoints:
            path = endpoint.get("path", "")
            method = endpoint.get("method", "")
            
            # Check for inconsistent naming
            if "_" in path and "-" in path:
                issues.append(f"Inconsistent naming: {path} uses both underscores and hyphens")
                scores["naming"] -= 5
            
            # Check for missing descriptions
            if not endpoint.get("description"):
                issues.append(f"Missing description: {method} {path}")
                scores["documentation"] -= 10
            
            # Check REST conventions
            if method == "GET" and "create" in path.lower():
                issues.append(f"Questionable design: {method} {path} - GET with 'create' in path")
                scores["design"] -= 10
            
            if method == "DELETE" and not any(x in path for x in ["{", ":"]):
                suggestions.append(f"Consider: {method} {path} - DELETE without path parameter might be dangerous")
        
        # Calculate overall score
        overall = int(sum(scores.values()) / len(scores))
        
        # Add general suggestions
        if scores["documentation"] < 80:
            suggestions.append("Add descriptions to endpoints with missing documentation")
        if scores["consistency"] < 80:
            suggestions.append("Standardize naming conventions across all endpoints")
        
        return QualityScore(
            overall_score=max(0, min(100, overall)),
            categories=scores,
            issues=issues[:10],  # Limit issues
            suggestions=suggestions[:5]
        )
    
    async def _generate(self, prompt: str) -> str:
        """Generate text using the AI model."""
        if not self.model:
            return "{}"
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return "{}"
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from AI response, handling markdown code blocks."""
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1])
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return {}
    
    def _generate_template_examples(
        self,
        endpoint: Dict[str, Any],
        languages: List[str]
    ) -> List[GeneratedExample]:
        """Generate basic template examples without AI."""
        examples = []
        path = endpoint.get("path", "/endpoint")
        method = endpoint.get("method", "GET")
        
        if "curl" in languages:
            examples.append(GeneratedExample(
                language="curl",
                code=f'curl -X {method} "https://api.example.com{path}" \\\n  -H "Authorization: Bearer YOUR_TOKEN"',
                description="Using cURL"
            ))
        
        if "python" in languages:
            examples.append(GeneratedExample(
                language="python",
                code=f'''import requests

response = requests.{method.lower()}(
    "https://api.example.com{path}",
    headers={{"Authorization": "Bearer YOUR_TOKEN"}}
)
print(response.json())''',
                description="Using Python requests"
            ))
        
        if "javascript" in languages:
            examples.append(GeneratedExample(
                language="javascript",
                code=f'''const response = await fetch("https://api.example.com{path}", {{
  method: "{method}",
  headers: {{
    "Authorization": "Bearer YOUR_TOKEN"
  }}
}});
const data = await response.json();
console.log(data);''',
                description="Using JavaScript fetch"
            ))
        
        return examples


# Singleton instance
advanced_ai_service = AdvancedAIService()
