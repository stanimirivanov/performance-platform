"""System metric collectors."""

from __future__ import annotations

import logging
import time
from typing import Any

import psutil

from perfeng.integration.models import Snapshot
from perfeng.integration.protocols import MetricCollector

logger = logging.getLogger(__name__)


class CpuCollector:
    def collect(self) -> list[Snapshot]:
        return [
            Snapshot(
                resource_type="cpu",
                value_current=psutil.cpu_percent(interval=None),
                unit="percent",
                test_phase="steady",
                attributes={},
            )
        ]


class MemoryCollector:
    def collect(self) -> list[Snapshot]:
        mem = psutil.virtual_memory()
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
    def __init__(self, path: str = "/"):
        self._path = path

    def collect(self) -> list[Snapshot]:
        disk = psutil.disk_usage(self._path)
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
    """Collects network I/O rates (bytes/sec) rather than cumulative counters."""

    def __init__(self) -> None:
        self._last_counters: Any | None = None
        self._last_time: float | None = None

    def collect(self) -> list[Snapshot]:
        counters = psutil.net_io_counters()
        now = time.monotonic()
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

    def __init__(self, collectors: list[MetricCollector]):
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
