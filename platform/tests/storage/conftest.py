"""Pytest fixtures for the entire test suite."""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from perfeng.core.config import settings
from perfeng.storage.models import *  # noqa: F403

# ---------------------------------------------------------------------------
# Database fixtures (integration tests)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine and run migrations."""
    # Use a separate database for tests, e.g., metadata_test
    test_db_url = settings.database_url.replace("/metadata", "/metadata_test")
    engine = create_async_engine(test_db_url, poolclass=NullPool)

    # Create the test database if it doesn't exist
    # This assumes the PostgreSQL server is reachable and you have permissions.
    # We'll run a simple SQL to create the database.

    async with engine.begin() as _conn:
        # Check if database exists; if not, create it
        # Note: this requires connecting to the 'postgres' database first.
        # For simplicity, we'll assume the database already exists.
        pass

    # Run migrations
    # Assuming migrations are in db/migrations and can be applied via asyncpg
    # We'll use a simple approach: run the migration files
    from scripts.run_migrations import run_migrations

    # Set environment variable for migrations
    os.environ["DATABASE_URL"] = test_db_url
    await run_migrations(reset=True)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an AsyncSession for a test, rolling back after each test."""
    async_session_factory = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session_factory() as session:
        # Begin a nested transaction to rollback after test
        async with session.begin():
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
