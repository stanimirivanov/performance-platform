"""Unit tests for ResourceUsageSampler (new design)."""

import asyncio

import pytest

from perfeng.integration.collectors import CpuCollector
from perfeng.integration.models import Snapshot
from perfeng.integration.sampling import ResourceUsageSampler
from tests.unit.integration.test_collectors import FakePsutil


class FakeSnapshotRepository:
    def __init__(self):
        self.saved: list[Snapshot] = []

    async def post_snapshots(self, run_id: str, snapshots: list[Snapshot]) -> None:
        self.saved.extend(snapshots)

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_sampler_collects_and_posts_snapshots():
    fake_repo = FakeSnapshotRepository()
    sampler = ResourceUsageSampler(
        run_id="r-123",
        base_url="http://unused",
        interval_seconds=0.01,
        collector=CpuCollector(),
        repository=fake_repo,
    )
    await sampler.start()
    await asyncio.sleep(0.05)
    await sampler.stop()

    assert len(fake_repo.saved) > 0
    # Verify snapshot structure
    snapshot = fake_repo.saved[0]
    assert snapshot.resource_type == "cpu"
    assert snapshot.value_current is not None


@pytest.mark.asyncio
async def test_sampler_context_manager_and_tick():
    repo = FakeSnapshotRepository()
    sampler = ResourceUsageSampler(
        run_id="r-1",
        base_url="http://unused",
        interval_seconds=0.01,
        collector=CpuCollector(psutil_module=FakePsutil(cpu=12.3)),
        repository=repo,
    )
    async with sampler:
        await asyncio.sleep(0.05)
    assert len(repo.saved) > 0
    assert repo.saved[0].value_current == 12.3
