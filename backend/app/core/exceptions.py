from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.core.logger import logger

async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for validation errors.
    """
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": exc.errors()
        }
    )

async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handler for database errors.
    """
    logger.error(f"Database error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database Error",
            "message": "Service temporarily unavailable.",
            "error": str(exc)
        }
    )
