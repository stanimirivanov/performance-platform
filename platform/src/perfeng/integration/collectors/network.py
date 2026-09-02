"""Network I/O rate collector."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import psutil

from perfeng.integration.models import Snapshot


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
