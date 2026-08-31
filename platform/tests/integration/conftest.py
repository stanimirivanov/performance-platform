"""Integration test fixtures."""

import os
from collections.abc import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from perfeng.core.config import settings
from perfeng.metadata.collector import MetadataCollector
from perfeng.metadata.config import load_collector_config


@pytest.fixture
def integration_collector() -> MetadataCollector:
    """Return a collector configured for the 'test' environment."""
    config = load_collector_config("test")
    return MetadataCollector(config=config)


@pytest_asyncio.fixture(scope="session")
async def test_postgres_container() -> str:
    """Create (if necessary) and return the test database DSN.

    Uses the application's default database URL as a starting point,
    but replaces the database name with `metadata_test`.
    """
    # Original async DSN from settings
    async_dsn = settings.database_url
    # Convert to plain postgresql:// for asyncpg (for maintenance operations)
    plain_dsn = async_dsn.replace("postgresql+asyncpg://", "postgresql://")

    # Extract base URL without database name
    base_dsn = plain_dsn.rsplit("/", 1)[0]
    test_db_name = "metadata_test"

    # Connect to the 'postgres' maintenance database to create test DB if needed
    maintenance_dsn = f"{base_dsn}/postgres"
    conn = await asyncpg.connect(dsn=maintenance_dsn)
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", test_db_name)
        if not exists:
            # Quote identifier? test_db_name is safe.
            await conn.execute(f"CREATE DATABASE {test_db_name}")
    finally:
        await conn.close()

    # Now prepare the test DSN (async variant for SQLAlchemy async engine)
    test_async_dsn = async_dsn.rsplit("/", 1)[0] + f"/{test_db_name}"

    # Run migrations on the test DB (using the sync DSN for the script)
    # We'll set environment variable and call the migration script.
    os.environ["DATABASE_URL"] = plain_dsn.rsplit("/", 1)[0] + f"/{test_db_name}"
    from scripts.run_migrations import run_migrations

    await run_migrations(reset=True)

    return test_async_dsn


@pytest_asyncio.fixture
async def db_session(test_postgres_container) -> AsyncGenerator[AsyncSession, None]:
    """Provide an AsyncSession that rolls back after each test."""
    engine = create_async_engine(test_postgres_container)
    async_session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    async with async_session_factory() as session, session.begin():
        yield session
        await session.rollback()
    await engine.dispose()
