"""Unit tests for ResourceUsageSampler."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import Response

from perfeng.integration.sampling import ResourceUsageSampler


@pytest_asyncio.fixture
async def sampler_with_mock_client():
    run_id = str(uuid4())
    mock_client = AsyncMock()
    mock_client.post.return_value = Response(
        status_code=201,
        json={"snapshot_id": str(uuid4())},
        request=MagicMock(),
    )
    sampler = ResourceUsageSampler(
        run_id=run_id,
        base_url="http://test",
        interval_seconds=0.01,  # very fast for testing
        client=mock_client,
    )
    yield sampler, mock_client
    # Ensure sampler is stopped
    await sampler.stop()
    await sampler._client.aclose()


@pytest.mark.asyncio
async def test_collect_snapshots_returns_metrics():
    sampler = ResourceUsageSampler(
        run_id="dummy",
        base_url="http://test",
        interval_seconds=0.01,
        client=AsyncMock(),
    )
    snapshots = sampler._collect_snapshots()
    assert isinstance(snapshots, list)
    assert len(snapshots) == 4  # cpu, memory, disk, network

    resource_types = {s["resource_type"] for s in snapshots}
    assert resource_types == {"cpu", "memory", "disk", "network"}

    for snap in snapshots:
        assert "value_current" in snap
        assert "unit" in snap
        assert "test_phase" in snap
        assert "attributes" in snap  # renamed from metadata
        assert isinstance(snap["attributes"], dict)


@pytest.mark.asyncio
async def test_start_and_stop_posts_snapshots(sampler_with_mock_client):
    sampler, mock_client = sampler_with_mock_client
    await sampler.start()
    # Wait a bit to allow at least one snapshot to be sent
    await asyncio.sleep(0.05)
    await sampler.stop()

    # Verify that at least one POST was made to the snapshots endpoint
    assert mock_client.post.await_count >= 1
    call_args = mock_client.post.call_args_list[0]
    assert call_args[0][0] == f"http://test/api/v1/runs/{sampler.run_id}/snapshots/"
    assert call_args[1]["json"]["resource_type"] == "cpu"


@pytest.mark.asyncio
async def test_sampler_context_manager():
    run_id = str(uuid4())
    mock_client = AsyncMock()
    mock_client.post.return_value = Response(
        status_code=201,
        json={"snapshot_id": str(uuid4())},
        request=MagicMock(),
    )
    sampler = ResourceUsageSampler(
        run_id=run_id,
        base_url="http://test",
        interval_seconds=0.01,
        client=mock_client,
    )
    async with sampler as s:
        assert s is sampler
        await asyncio.sleep(0.03)
    assert mock_client.post.await_count >= 1
    mock_client.aclose.assert_awaited_once()
