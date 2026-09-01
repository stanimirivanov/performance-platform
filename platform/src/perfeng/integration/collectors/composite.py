"""Composite collector that aggregates multiple collectors."""

from __future__ import annotations

import logging

from perfeng.integration.models import Snapshot
from perfeng.integration.protocols import MetricCollector

logger = logging.getLogger(__name__)


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
