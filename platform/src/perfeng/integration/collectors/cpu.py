"""CPU usage collector."""

from __future__ import annotations

from typing import Any

import psutil

from perfeng.integration.models import Snapshot


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
