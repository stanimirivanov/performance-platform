"""Unit tests for SnapshotService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.models import ResourceSnapshots
from perfeng.storage.repositories.snapshot_repository import SnapshotRepository
from perfeng.storage.schemas import SnapshotCreate, SnapshotFilter, SnapshotResponse
from perfeng.storage.services.snapshot_service import SnapshotService


@pytest.fixture
def mock_snapshot_repo():
    return Mock(spec=SnapshotRepository)


@pytest.fixture
def service(mock_snapshot_repo):
    return SnapshotService(mock_snapshot_repo)


def make_fake_snapshot(**kwargs):
    defaults = {
        "snapshot_id": uuid4(),
        "run_id": uuid4(),
        "resource_type": "cpu",
        "value_current": 1.0,
        "snapshot_time": datetime.now(UTC),
        "attributes": {},
    }
    defaults.update(kwargs)
    return ResourceSnapshots(**defaults)


@pytest.mark.asyncio
async def test_create_snapshot(service, mock_snapshot_repo):
    session = AsyncMock(spec=AsyncSession)
    run_id = uuid4()
    data = SnapshotCreate(resource_type="cpu", value_current=5.0)
    fake_snapshot = make_fake_snapshot(run_id=run_id)
    mock_snapshot_repo.create_for_run = AsyncMock(return_value=fake_snapshot)

    result = await service.create_snapshot(session, run_id, data)

    mock_snapshot_repo.create_for_run.assert_awaited_once_with(session, run_id, data)
    assert isinstance(result, SnapshotResponse)
    assert result.snapshot_id == fake_snapshot.snapshot_id


@pytest.mark.asyncio
async def test_list_snapshots(service, mock_snapshot_repo):
    session = AsyncMock(spec=AsyncSession)
    run_id = uuid4()
    filters = SnapshotFilter(resource_type="cpu", limit=10, offset=0)
    fake_snaps = [make_fake_snapshot()]
    mock_snapshot_repo.list_by_run = AsyncMock(return_value=fake_snaps)

    result = await service.list_snapshots(session, run_id, filters)

    mock_snapshot_repo.list_by_run.assert_awaited_once_with(session, run_id, filters)
    assert len(result) == 1
    assert isinstance(result[0], SnapshotResponse)
