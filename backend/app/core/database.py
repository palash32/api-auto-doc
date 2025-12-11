"""Database configuration and session management."""

from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Determine database type from URL
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite for local development
    SYNC_DATABASE_URL = settings.DATABASE_URL
    ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    # PostgreSQL for production
    ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    SYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+pg8000://")

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Asynchronous engine (for FastAPI)
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite doesn't need connection pooling
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL with connection pooling
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.DEBUG,
    )

# Session factories
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_async_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db():
    """
    Dependency for getting sync database sessions.
    Used in Celery workers and synchronous contexts.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Alias for compatibility
get_async_session = get_async_db
