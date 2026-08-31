"""Local system detection."""

from __future__ import annotations

import os
import platform

import psutil

from perfeng.metadata.detectors.types import NodeInfo, NodeResources


class LocalNodeDetector:
    """Detect information about the machine this code runs on."""

    def detect(self) -> NodeInfo:
        """Gather OS, kernel, architecture, and resource information."""
        return NodeInfo(
            os=platform.system(),
            kernel=platform.release(),
            architecture=platform.machine(),
            resources=self._detect_resources(),
        )

    def _detect_resources(self) -> NodeResources:
        try:
            return NodeResources(
                cpu_cores=psutil.cpu_count() or 1,
                memory_total_gb=psutil.virtual_memory().total / (1024**3),
                disk_total_gb=psutil.disk_usage("/").total / (1024**3),
            )
        except Exception:
            # psutil may fail in restricted environments (e.g. containers)
            return NodeResources(cpu_cores=os.cpu_count() or 1)
