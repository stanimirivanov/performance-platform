"""Integration tests for RunRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.repositories import EnvironmentRepository, RunRepository
from perfeng.storage.schemas import EnvironmentCreate, RunCreate, RunFilter, RunUpdate


@pytest.mark.asyncio
async def test_create_run(db_session: AsyncSession):
    repo = RunRepository()
    run_data = RunCreate(test_name="test-run", status="pending")
    run = await repo.create(db_session, run_data)

    assert run.run_id is not None
    assert run.test_name == "test-run"
    # Retrieve from DB to confirm persistence
    retrieved = await repo.get_by_id(db_session, run.run_id)
    assert retrieved is not None
    assert retrieved.test_name == "test-run"


@pytest.mark.asyncio
async def test_get_by_id_returns_environment(db_session: AsyncSession):
    repo = RunRepository()
    env_repo = EnvironmentRepository()

    # Create a run and environment
    run_data = RunCreate(test_name="with-env", status="running")
    run = await repo.create(db_session, run_data)

    env_data = EnvironmentCreate(fingerprint_hash="abc123", cluster_name="local")
    await env_repo.create_for_run(db_session, run.run_id, env_data)

    retrieved = await repo.get_by_id(db_session, run.run_id)
    assert retrieved is not None
    assert retrieved.environments is not None
    assert retrieved.environments.cluster_name == "local"


@pytest.mark.asyncio
async def test_update_run(db_session: AsyncSession):
    repo = RunRepository()
    run_data = RunCreate(test_name="update-me", status="pending")
    run = await repo.create(db_session, run_data)

    update_data = RunUpdate(status="completed", success_rate=0.99)
    updated = await repo.update(db_session, run.run_id, update_data)

    assert updated is not None
    assert updated.status == "completed"
    assert updated.success_rate == 0.99


@pytest.mark.asyncio
async def test_list_with_filters(db_session: AsyncSession):
    repo = RunRepository()

    # Create multiple runs with different statuses and names
    for i in range(3):
        run_data = RunCreate(
            test_name=f"run-{i}",
            status="completed" if i % 2 == 0 else "failed",
        )
        await repo.create(db_session, run_data)

    # Filter by status
    filters = RunFilter(status="completed", limit=10, offset=0)
    runs = await repo.list_with_filters(db_session, filters)
    assert len(runs) == 2
    assert all(r.status == "completed" for r in runs)

    # Filter by test_name contains
    filters = RunFilter(test_name="run-1", limit=10, offset=0)
    runs = await repo.list_with_filters(db_session, filters)
    assert len(runs) == 1
    assert runs[0].test_name == "run-1"


@pytest.mark.asyncio
async def test_list_with_filters_by_fingerprint(db_session: AsyncSession):
    repo = RunRepository()
    env_repo = EnvironmentRepository()

    # Create a run and give it an environment with a unique fingerprint
    run_with_env = await repo.create(
        db_session, RunCreate(test_name="with-env", status="completed")
    )
    fingerprint = "unique-fingerprint-123"
    await env_repo.create_for_run(
        db_session,
        run_with_env.run_id,
        EnvironmentCreate(fingerprint_hash=fingerprint, cluster_name="local"),
    )

    # Create another run without environment (or different fingerprint)
    _run_without_env = await repo.create(
        db_session, RunCreate(test_name="no-env", status="completed")
    )

    # Filter by fingerprint
    filters = RunFilter(fingerprint=fingerprint, limit=10, offset=0)
    runs = await repo.list_with_filters(db_session, filters)

    assert len(runs) == 1
    assert runs[0].run_id == run_with_env.run_id
