"""Unit tests for RunService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.models import TestRuns
from perfeng.storage.repositories.environment_repository import EnvironmentRepository
from perfeng.storage.repositories.run_repository import RunRepository
from perfeng.storage.schemas import RunCreate, RunCreateResponse, RunFilter, RunResponse, RunUpdate
from perfeng.storage.services.run_service import RunService


@pytest.fixture
def mock_run_repo():
    return Mock(spec=RunRepository)


@pytest.fixture
def mock_env_repo():
    return Mock(spec=EnvironmentRepository)


@pytest.fixture
def service(mock_run_repo, mock_env_repo):
    return RunService(mock_run_repo, mock_env_repo)


# Helper to create a fake TestRuns with all required fields
def make_fake_run(**kwargs):
    defaults = {
        "run_id": uuid4(),
        "test_name": "test",
        "status": "pending",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return TestRuns(**defaults)


@pytest.mark.asyncio
async def test_create_run(service, mock_run_repo, mock_env_repo):
    session = AsyncMock(spec=AsyncSession)
    run_data = RunCreate(test_name="test", status="pending")
    fake_run = make_fake_run(test_name="test", status="pending")
    mock_run_repo.create = AsyncMock(return_value=fake_run)

    result = await service.create_run(session, run_data)

    mock_run_repo.create.assert_awaited_once_with(session, run_data)
    assert isinstance(result, RunCreateResponse)
    assert result.run_id == fake_run.run_id


@pytest.mark.asyncio
async def test_get_run(service, mock_run_repo):
    session = AsyncMock(spec=AsyncSession)
    run_id = uuid4()
    fake_run = make_fake_run(run_id=run_id, status="completed")
    mock_run_repo.get_by_id = AsyncMock(return_value=fake_run)

    result = await service.get_run(session, run_id)

    mock_run_repo.get_by_id.assert_awaited_once_with(session, run_id)
    assert isinstance(result, RunResponse)
    assert result.run_id == run_id
    assert result.created_at is not None
    assert result.updated_at is not None


@pytest.mark.asyncio
async def test_update_run(service, mock_run_repo):
    session = AsyncMock(spec=AsyncSession)
    run_id = uuid4()
    update_data = RunUpdate(status="completed")
    fake_updated_run = make_fake_run(run_id=run_id, status="completed")
    mock_run_repo.update = AsyncMock(return_value=fake_updated_run)

    result = await service.update_run(session, run_id, update_data)

    mock_run_repo.update.assert_awaited_once_with(session, run_id, update_data)
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_list_runs(service, mock_run_repo):
    session = AsyncMock(spec=AsyncSession)
    filters = RunFilter(status="completed", limit=10, offset=0)
    fake_runs = [make_fake_run(status="completed")]
    mock_run_repo.list_with_filters = AsyncMock(return_value=fake_runs)

    result = await service.list_runs(session, filters)

    mock_run_repo.list_with_filters.assert_awaited_once_with(session, filters)
    assert len(result) == 1
    assert isinstance(result[0], RunResponse)
