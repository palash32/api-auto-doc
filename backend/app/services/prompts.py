"""Prompt templates for Gemini AI documentation generation."""

API_DOC_PROMPT = """
You are an expert API documentation generator. Your task is to analyze the provided code snippet and generate structured API documentation in JSON format.

LANGUAGE: {language}
CODE:
```
{code}
```

INSTRUCTIONS:
1. Analyze the code to identify the API endpoint, HTTP method, path, parameters, and response structure.
2. Generate a comprehensive summary and detailed description.
3. Identify all request parameters (path, query, body) and their types.
4. Infer potential response status codes and body structures.
5. Determine if authentication is required.
6. OUTPUT MUST BE VALID JSON ONLY. Do not include markdown formatting or explanations outside the JSON.

JSON STRUCTURE:
{{
    "summary": "Short summary of what the endpoint does",
    "description": "Detailed explanation of the endpoint's functionality, including business logic if visible.",
    "method": "GET/POST/PUT/DELETE/etc",
    "path": "/api/path/to/resource",
    "parameters": [
        {{
            "name": "param_name",
            "in": "path/query/header/cookie",
            "type": "string/integer/boolean/etc",
            "required": true/false,
            "description": "Description of the parameter"
        }}
    ],
    "request_body": {{
        "description": "Description of request body",
        "schema": {{ ... }}  # JSON schema representation if possible
    }},
    "responses": [
        {{
            "status_code": 200,
            "description": "Success response description",
            "schema": {{ ... }} # JSON schema of response
        }}
    ],
    "auth_required": true/false,
    "auth_type": "Bearer/API Key/OAuth/None",
    "tags": ["tag1", "tag2"]
}}
"""
