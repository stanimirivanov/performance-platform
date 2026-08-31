"""Resource usage sampler that posts snapshots to the storage API."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

import httpx
import psutil

logger = logging.getLogger(__name__)


class ResourceUsageSampler:
    """Periodically collect system metrics and POST them as snapshots."""

    def __init__(
        self,
        run_id: str,
        base_url: str,
        interval_seconds: float = 5.0,
        client: httpx.AsyncClient | None = None,
    ):
        self.run_id = run_id
        self.base_url = base_url.rstrip("/")
        self.interval = interval_seconds
        self._client = client or httpx.AsyncClient()
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """Start the sampling loop (non‑blocking)."""
        self._stop_event.clear()
        asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Signal the sampler to stop and wait for the loop to finish."""
        self._stop_event.set()
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.sleep(0)

    async def _run_loop(self) -> None:
        """Continuously collect and send snapshots until stopped."""
        while not self._stop_event.is_set():
            snapshots = self._collect_snapshots()
            for snapshot in snapshots:
                try:
                    await self._post_snapshot(snapshot)
                except httpx.HTTPError as exc:
                    logger.error("Failed to post snapshot: %s", exc)
            await asyncio.sleep(self.interval)

    def _collect_snapshots(self) -> list[dict[str, Any]]:
        """Collect CPU, memory, disk, and network metrics as separate snapshots."""
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()

        snapshots = [
            {
                "resource_type": "cpu",
                "value_current": cpu_percent,
                "unit": "percent",
                "test_phase": "steady",
                "attributes": {},
            },
            {
                "resource_type": "memory",
                "value_current": mem.percent,
                "unit": "percent",
                "test_phase": "steady",
                "attributes": {},
            },
            {
                "resource_type": "disk",
                "value_current": disk.percent,
                "unit": "percent",
                "test_phase": "steady",
                "attributes": {},
            },
            {
                "resource_type": "network",
                "value_current": net.bytes_sent,
                "unit": "bytes",
                "test_phase": "steady",
                "attributes": {"bytes_recv": net.bytes_recv},
            },
        ]
        return snapshots

    async def _post_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Send the snapshot to the API."""
        response = await self._client.post(
            f"{self.base_url}/api/v1/runs/{self.run_id}/snapshots/",
            json=snapshot,
        )
        response.raise_for_status()

    async def __aenter__(self) -> ResourceUsageSampler:
        await self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.stop()
        await self._client.aclose()
