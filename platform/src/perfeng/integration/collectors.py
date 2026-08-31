"""System metric collectors with injectable dependencies."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import psutil

from perfeng.integration.models import Snapshot
from perfeng.integration.protocols import MetricCollector

logger = logging.getLogger(__name__)


class CpuCollector:
    """Collects CPU usage percentage."""

    def __init__(self, psutil_module: Any = psutil) -> None:
        self._psutil = psutil_module

    def collect(self) -> list[Snapshot]:
        return [
            Snapshot(
                resource_type="cpu",
                value_current=self._psutil.cpu_percent(interval=None),
                unit="percent",
                test_phase="steady",
                attributes={},
            )
        ]


class MemoryCollector:
    """Collects memory usage percentage and totals."""

    def __init__(self, psutil_module: Any = psutil) -> None:
        self._psutil = psutil_module

    def collect(self) -> list[Snapshot]:
        mem = self._psutil.virtual_memory()
        return [
            Snapshot(
                resource_type="memory",
                value_current=mem.percent,
                unit="percent",
                test_phase="steady",
                attributes={
                    "total": mem.total,
                    "available": mem.available,
                },
            )
        ]


class DiskCollector:
    """Collects disk usage for a given path."""

    def __init__(self, path: str = "/", psutil_module: Any = psutil) -> None:
        self._path = path
        self._psutil = psutil_module

    def collect(self) -> list[Snapshot]:
        disk = self._psutil.disk_usage(self._path)
        return [
            Snapshot(
                resource_type="disk",
                value_current=disk.percent,
                unit="percent",
                test_phase="steady",
                attributes={"path": self._path, "total": disk.total, "used": disk.used},
            )
        ]


class NetworkCollector:
    """Collects network I/O rates (bytes/sec) rather than cumulative counters.

    Dependencies are injectable:
        - `psutil_module`: provides `net_io_counters()`.
        - `time_source`: provides monotonic time for rate calculation.
    """

    def __init__(
        self,
        psutil_module: Any = psutil,
        time_source: Callable[[], float] = time.monotonic,
    ) -> None:
        self._psutil = psutil_module
        self._time_source = time_source
        self._last_counters: Any | None = None
        self._last_time: float | None = None

    def collect(self) -> list[Snapshot]:
        counters = self._psutil.net_io_counters()
        now = self._time_source()
        snapshots: list[Snapshot] = []

        if self._last_counters is not None and self._last_time is not None:
            dt = now - self._last_time
            if dt > 0:
                sent_rate = (counters.bytes_sent - self._last_counters.bytes_sent) / dt
                recv_rate = (counters.bytes_recv - self._last_counters.bytes_recv) / dt

                snapshots.append(
                    Snapshot(
                        resource_type="network",
                        value_current=round(sent_rate, 2),
                        unit="bytes_per_second",
                        test_phase="steady",
                        attributes={"direction": "sent"},
                    )
                )
                snapshots.append(
                    Snapshot(
                        resource_type="network",
                        value_current=round(recv_rate, 2),
                        unit="bytes_per_second",
                        test_phase="steady",
                        attributes={"direction": "recv"},
                    )
                )

        self._last_counters = counters
        self._last_time = now
        return snapshots


class CompositeCollector:
    """Aggregates multiple collectors, isolating failures."""

    def __init__(self, collectors: list[MetricCollector]) -> None:
        self._collectors = collectors

    def collect(self) -> list[Snapshot]:
        snapshots: list[Snapshot] = []
        for collector in self._collectors:
            try:
                snapshots.extend(collector.collect())
            except Exception:
                logger.exception(
                    "Collector %s failed; continuing with others", type(collector).__name__
                )
        return snapshots
