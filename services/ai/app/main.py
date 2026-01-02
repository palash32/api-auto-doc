"""
AI Documentation Service - Main Application
FastAPI service for GPT-4 powered documentation generation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routes import health, generate
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Documentation Service",
    description="GPT-4 powered API documentation generation",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(generate.router, prefix="/generate", tags=["generate"])

@app.on_event("startup")
async def startup():
    logger.info("""
╔═══════════════════════════════════════════════════════════╗
║         AI Documentation Service - Python                  ║
╠═══════════════════════════════════════════════════════════╣
║  🚀 Server:     http://localhost:%s                       ║
║  🤖 Gemini:     %s                                        ║
╚═══════════════════════════════════════════════════════════╝
    """, settings.PORT, "configured" if settings.GEMINI_API_KEY else "NOT configured")

@app.get("/")
async def root():
    return {
        "service": "AI Documentation Service",
        "version": "2.0.0",
        "status": "operational",
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }
