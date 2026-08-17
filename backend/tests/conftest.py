"""Pytest fixtures — async DB, FastAPI client, and a fake user."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# IMPORTANT: install aiosqlite in dev requirements if not present
aiosqlite = pytest.importorskip("aiosqlite", reason="aiosqlite is required for the test suite")

from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db.session import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402


# Pydantic v2's EmailStr uses email-validator which rejects `.local`.
# We use a real-looking domain (`.test`) in fixtures instead.


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    # Import models to register them on Base.metadata
    import app.models  # noqa: F401
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture()
async def db_session(engine) -> AsyncIterator[AsyncSession]:
    Session = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with Session() as session:
        yield session


@pytest_asyncio.fixture()
async def client(db_session) -> AsyncIterator[AsyncClient]:
    async def _override():
        yield db_session
    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def user(db_session) -> User:
    # Use a real-looking domain so email-validator's deliverability check
    # is happy.
    u = User(
        email="test@clipforge.example",
        name="Tester",
        hashed_password=hash_password("test1234"),
        role="admin",
        is_active=True,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture()
async def auth_headers(user) -> dict[str, str]:
    token = create_access_token(user.id, extra={"role": user.role})
    return {"Authorization": f"Bearer {token}"}
