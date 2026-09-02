"""Memory usage collector."""

from __future__ import annotations

from typing import Any

import psutil

from perfeng.integration.models import Snapshot


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
