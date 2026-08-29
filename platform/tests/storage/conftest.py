import os
from collections.abc import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from perfeng.core.config import settings
from perfeng.storage.models import *  # noqa: F403


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database, run migrations, and yield an async engine."""
    # 1. Prepare URLs
    async_url = settings.database_url
    sync_url = async_url.replace("postgresql+asyncpg://", "postgresql://")
    sync_url_test = sync_url.rsplit("/", 1)[0] + "/metadata_test"
    async_url_test = async_url.rsplit("/", 1)[0] + "/metadata_test"
    maintenance_sync_url = sync_url.rsplit("/", 1)[0] + "/postgres"

    # 2. Create test database if missing
    conn = await asyncpg.connect(dsn=maintenance_sync_url)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", "metadata_test"
        )
        if not exists:
            await conn.execute("CREATE DATABASE metadata_test")
    finally:
        await conn.close()

    # 3. Run migrations (reset=True drops/recreates schemas)
    os.environ["DATABASE_URL"] = sync_url_test  # migration script expects plain DSN
    from scripts.run_migrations import run_migrations

    await run_migrations(reset=True)

    # 4. Create async engine for the test database
    engine = create_async_engine(async_url_test, poolclass=NullPool)

    yield engine

    # 5. Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an AsyncSession that rolls back after each test."""
    async_session_factory = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session_factory() as session, session.begin():
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest.fixture
def client(db_session):
    """Create a FastAPI TestClient with overridden database session."""
    from fastapi.testclient import TestClient

    from perfeng.api.app import create_app
    from perfeng.storage.database import get_session

    app = create_app()

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
