# API Documentation AI Service

Python FastAPI service for AI-powered documentation generation.

## Features

- 🤖 GPT-4 documentation generation
- 📝 Code analysis and summary extraction
- 💰 Cost tracking per request
- 🔄 Fallback to basic extraction when AI fails

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 3002
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /generate | Generate documentation for endpoint |
| POST | /batch | Batch generate for multiple endpoints |
