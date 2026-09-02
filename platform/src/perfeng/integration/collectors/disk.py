"""Disk usage collector."""

from __future__ import annotations

from typing import Any

import psutil

from perfeng.integration.models import Snapshot


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
