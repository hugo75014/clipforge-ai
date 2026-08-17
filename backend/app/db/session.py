"""Async SQLAlchemy engine, session factory, and Base."""

from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _build_engine() -> AsyncEngine:
    url = settings.database_url
    # SQLite (used in tests) doesn't support pool sizing
    kwargs: dict = {"echo": False, "future": True}
    if not url.startswith("sqlite"):
        kwargs.update(pool_size=10, max_overflow=20, pool_pre_ping=True)
    return create_async_engine(url, **kwargs)


engine: AsyncEngine = _build_engine()
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (dev convenience; production uses Alembic)."""
    # Import all models so they're registered on Base.metadata
    from app.models import (  # noqa: F401
        brand_kit,
        clip,
        export,
        job,
        project,
        template,
        transcript,
        user,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
