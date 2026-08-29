"""Unit tests for RunService."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from perfeng.storage.filters import RunFilter
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.models import TestRuns
from perfeng.storage.repositories.environment_repository import EnvironmentRepository
from perfeng.storage.repositories.run_repository import RunRepository
from perfeng.storage.schemas import RunCreate, RunCreateResponse, RunResponse, RunUpdate
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


@pytest.mark.asyncio
async def test_create_run(service, mock_run_repo, mock_env_repo):
    session = AsyncMock(spec=AsyncSession)
    run_data = RunCreate(test_name="test", status="pending")
    fake_run = TestRuns(run_id=uuid4(), test_name="test", status="pending")
    mock_run_repo.create = AsyncMock(return_value=fake_run)

    result = await service.create_run(session, run_data)

    mock_run_repo.create.assert_awaited_once_with(session, run_data)
    assert isinstance(result, RunCreateResponse)
    assert result.run_id == fake_run.run_id


@pytest.mark.asyncio
async def test_get_run(service, mock_run_repo):
    session = AsyncMock(spec=AsyncSession)
    run_id = uuid4()
    fake_run = TestRuns(run_id=run_id, test_name="test", status="completed")
    mock_run_repo.get_by_id = AsyncMock(return_value=fake_run)

    result = await service.get_run(session, run_id)

    mock_run_repo.get_by_id.assert_awaited_once_with(session, run_id)
    assert isinstance(result, RunResponse)
    assert result.run_id == run_id


@pytest.mark.asyncio
async def test_update_run(service, mock_run_repo):
    session = AsyncMock(spec=AsyncSession)
    run_id = uuid4()
    update_data = RunUpdate(status="completed")
    fake_updated_run = TestRuns(run_id=run_id, status="completed")
    mock_run_repo.update = AsyncMock(return_value=fake_updated_run)

    result = await service.update_run(session, run_id, update_data)

    mock_run_repo.update.assert_awaited_once_with(session, run_id, update_data)
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_list_runs(service, mock_run_repo):
    session = AsyncMock(spec=AsyncSession)
    filters = RunFilter(status="completed", limit=10, offset=0)
    fake_runs = [TestRuns(run_id=uuid4(), status="completed")]
    mock_run_repo.list_with_filters = AsyncMock(return_value=fake_runs)

    result = await service.list_runs(session, filters)

    mock_run_repo.list_with_filters.assert_awaited_once_with(session, filters)
    assert len(result) == 1
    assert isinstance(result[0], RunResponse)
