"""Facade for resource usage sampling."""

from __future__ import annotations

import logging
from typing import Any

from perfeng.integration.collectors import (
    CompositeCollector,
    CpuCollector,
    DiskCollector,
    MemoryCollector,
    NetworkCollector,
)
from perfeng.integration.infrastructure import IntervalScheduler
from perfeng.integration.protocols import MetricCollector, SnapshotRepository
from perfeng.integration.repositories import StorageSnapshotRepository

logger = logging.getLogger(__name__)


class ResourceUsageSampler:
    """Periodically collect system metrics and POST them as snapshots."""

    def __init__(
        self,
        run_id: str,
        base_url: str,
        interval_seconds: float = 5.0,
        collector: MetricCollector | None = None,
        repository: SnapshotRepository | None = None,
    ):
        self._run_id = run_id
        self._collector = collector or self._default_collector()
        self._repository = repository or StorageSnapshotRepository(base_url)
        self._scheduler = IntervalScheduler(
            interval_seconds=interval_seconds,
            callback=self._tick,
            name=f"sampler-{run_id}",
        )

    @staticmethod
    def _default_collector() -> MetricCollector:
        return CompositeCollector(
            [CpuCollector(), MemoryCollector(), DiskCollector(), NetworkCollector()]
        )

    async def _tick(self) -> None:
        snapshots = self._collector.collect()
        if not snapshots:
            return
        try:
            await self._repository.post_snapshots(self._run_id, snapshots)
        except Exception:
            logger.exception("Failed to post snapshots for run %s", self._run_id)

    async def start(self) -> None:
        """Start the sampling loop (non-blocking)."""
        await self._scheduler.start()

    async def stop(self) -> None:
        """Signal the sampler to stop and wait for the loop to finish."""
        await self._scheduler.stop()

    async def __aenter__(self) -> ResourceUsageSampler:
        await self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.stop()
        await self._repository.close()
