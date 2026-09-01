"""Unit tests for storage repositories."""

from unittest.mock import AsyncMock, Mock

import pytest

from perfeng.integration.models import Snapshot
from perfeng.integration.repositories import StorageSnapshotRepository


@pytest.mark.asyncio
async def test_post_snapshots():
    mock_client = AsyncMock()
    mock_client.post.return_value = Mock(status_code=200)
    mock_client.post.return_value.raise_for_status = Mock()
    mock_client.post.return_value.json.return_value = {"ok": True}

    repo = StorageSnapshotRepository(base_url="http://test", http_client=mock_client)
    snapshots = [
        Snapshot(
            resource_type="cpu",
            value_current=1.0,
            unit="percent",
            test_phase="steady",
            attributes={},
        ),
        Snapshot(
            resource_type="memory",
            value_current=2.0,
            unit="percent",
            test_phase="steady",
            attributes={},
        ),
    ]
    await repo.post_snapshots("run-1", snapshots)

    assert mock_client.post.await_count == 2
    # Expect full URL because ResilientHttpClient prepends base_url
    args, kwargs = mock_client.post.call_args_list[0]
    assert args[0] == "http://test/api/v1/runs/run-1/snapshots/"
    assert kwargs["json"]["resource_type"] == "cpu"
    assert kwargs["json"]["attributes"] == {}


@pytest.mark.asyncio
async def test_repository_close():
    mock_client = AsyncMock()
    repo = StorageSnapshotRepository(base_url="http://test", http_client=mock_client)
    await repo.close()
    mock_client.aclose.assert_awaited_once()
