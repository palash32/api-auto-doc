"""Main FastAPI application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import async_engine, Base
from app.core.logger import logger
from app.core.exceptions import (
    global_exception_handler, 
    validation_exception_handler,
    database_exception_handler
)

# Import routers
from app.api import endpoints, auth, webhooks, repositories, playground, team, branding, analytics, ai_enhance, versions, search, health, security, billing, enterprise, cicd, import_export, performance
from app.api import websocket as ws_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Automatically discover, document, and monitor all APIs across your organization's codebase",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

@app.on_event("startup")
async def startup():
    logger.info("🚀 Starting API Auto-Documentation Platform...")
    logger.info(f"📝 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔗 Frontend URL: {settings.FRONTEND_URL}")
    
    # Create database tables
    if settings.is_development:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created")


@app.on_event("shutdown")
async def shutdown():
    logger.info("👋 Shutting down...")

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)

# CORS middleware - MUST be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
    }


# API routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(endpoints.router, prefix="/api", tags=["Endpoints"])
app.include_router(repositories.router, prefix="/api/repositories", tags=["Repositories"])
app.include_router(playground.router, prefix="/api/playground", tags=["Playground"])
app.include_router(ws_router.router, tags=["WebSocket"])
app.include_router(team.router, prefix="/api/team", tags=["Team"])
app.include_router(branding.router, prefix="/api/branding", tags=["Branding"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(ai_enhance.router, prefix="/api/ai", tags=["AI Enhancement"])
app.include_router(versions.router, prefix="/api", tags=["Versions"])
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(health.router, prefix="/api", tags=["Health Monitoring"])
app.include_router(security.router, prefix="/api", tags=["Security"])
app.include_router(billing.router, prefix="/api", tags=["Billing"])
app.include_router(enterprise.router, prefix="/api", tags=["Enterprise"])
app.include_router(cicd.router, prefix="/api", tags=["CI/CD"])
app.include_router(import_export.router, prefix="/api", tags=["Import/Export"])
app.include_router(performance.router, prefix="/api", tags=["Performance"])
# app.include_router(apis.router, prefix="/api/apis", tags=["APIs"])
# app.include_router(documentation.router, prefix="/api/docs", tags=["Documentation"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )
