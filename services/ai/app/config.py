"""
Configuration settings for AI service
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import os
from dotenv import load_dotenv


# Find root .env file
# This file is at: services/ai/app/config.py
# Root is at: ./ (3 levels up from config.py)
CURRENT_FILE = Path(__file__).resolve()  # config.py
APP_DIR = CURRENT_FILE.parent  # app/
AI_SERVICE_DIR = APP_DIR.parent  # ai/
SERVICES_DIR = AI_SERVICE_DIR.parent  # services/
ROOT_DIR = SERVICES_DIR.parent  # project root
ROOT_ENV = ROOT_DIR / ".env"

# Load root .env file explicitly
if ROOT_ENV.exists():
    load_dotenv(ROOT_ENV, override=True)
    print(f"✅ Loaded .env from: {ROOT_ENV}")
else:
    print(f"⚠️ .env not found at: {ROOT_ENV}")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server
    PORT: int = 3002
    ENVIRONMENT: str = "development"
    
    # Google Gemini AI
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-pro"
    
    # Gateway callback
    GATEWAY_URL: str = "http://gateway:8000"
    
    class Config:
        extra = "ignore"


settings = Settings()

# Debug: Print if key is found
if settings.GEMINI_API_KEY:
    key_preview = settings.GEMINI_API_KEY[:15] + "..." if len(settings.GEMINI_API_KEY) > 15 else settings.GEMINI_API_KEY
    print(f"✅ GEMINI_API_KEY loaded: {key_preview}")
else:
    # Check if it's in os.environ directly
    if os.getenv("GEMINI_API_KEY"):
        print(f"🔧 Key in os.environ but not in settings")
    else:
        print(f"⚠️ GEMINI_API_KEY not found in environment!")
