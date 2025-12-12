"""Application configuration using Pydantic Settings."""

from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    class Config:
        case_sensitive = False
        extra = "ignore"
        env_file = ".env"
        env_file_encoding = "utf-8"

    # Application
    APP_NAME: str = "API Auto-Documentation Platform"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Google Gemini AI (formerly OpenAI)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-pro"  # or "gemini-1.5-pro" for more advanced features
    
    # Database URLs
    DATABASE_URL: str = "sqlite:///./apidoc.db"  # SQLite for local dev, PostgreSQL for production
    REDIS_URL: str = "redis://localhost:6379/0"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/auth/github/callback"
    
    @field_validator("GITHUB_CLIENT_ID")
    @classmethod
    def fix_github_client_id(cls, v):
        if v and v.startswith("Iv1."):
            return v.replace("Iv1.", "")
        return v
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    
    # GitLab OAuth
    GITLAB_CLIENT_ID: Optional[str] = None
    GITLAB_CLIENT_SECRET: Optional[str] = None
    
    # Bitbucket OAuth
    BITBUCKET_CLIENT_ID: Optional[str] = None
    BITBUCKET_CLIENT_SECRET: Optional[str] = None
    
    # Email
    SMTP_HOST: str = "smtp.sendgrid.net"
    SMTP_PORT: int = 587
    SMTP_USER: str = "apikey"
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "noreply@apidocplatform.com"
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_ID_TEAM: Optional[str] = None
    
    # Security
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://api-auto-doc.vercel.app",
        "https://api-auto-doc-palash32s-projects.vercel.app"
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "api-auto-doc.onrender.com"]
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = True
    
    # Feature Flags
    ENABLE_AI_DOCUMENTATION: bool = True
    ENABLE_HEALTH_MONITORING: bool = True
    ENABLE_DEPENDENCY_ANALYSIS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Storage
    S3_BUCKET_NAME: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: Optional[str] = None
    
    # Local Repository Storage
    REPO_STORAGE_PATH: str = "./temp_repos"

    # Webhook Configuration
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if v is None:
            return ["http://localhost:3000", "https://api-auto-doc.vercel.app"]
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"


# Global settings instance
settings = Settings()
