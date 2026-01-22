"""
SalonSync Database Connection
"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.app_settings import get_settings

settings = get_settings()

# Configure engine based on database type
engine_kwargs = {"pool_pre_ping": True}

# Only add pool settings for non-SQLite databases
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 1800
    engine_kwargs["pool_timeout"] = 30

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# =============================================================================
# Async Database Support
# =============================================================================

def _get_async_database_url() -> str:
    """Convert sync database URL to async format."""
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql+psycopg2://"):
        return db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("sqlite://"):
        return db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return db_url


_async_engine = None
_async_session_factory = None


def _get_async_engine():
    """Get or create async engine (lazy initialization)."""
    global _async_engine
    if _async_engine is None:
        async_kwargs = {"pool_pre_ping": True}
        if not settings.DATABASE_URL.startswith("sqlite"):
            async_kwargs["pool_size"] = 5
            async_kwargs["max_overflow"] = 10
            async_kwargs["pool_recycle"] = 1800
        _async_engine = create_async_engine(
            _get_async_database_url(),
            **async_kwargs
        )
    return _async_engine


def _get_async_session_factory():
    """Get or create async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=_get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


def get_db():
    """Dependency for FastAPI routes to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_session():
    """Dependency for FastAPI routes that need async database sessions."""
    async_session_factory = _get_async_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@contextmanager
def get_sync_db():
    """Context manager for sync database session outside FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
