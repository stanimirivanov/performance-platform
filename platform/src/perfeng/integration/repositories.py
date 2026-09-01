"""Repository implementations for storage API."""

from __future__ import annotations

import logging
from typing import Any

from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.integration.infrastructure import ResilientHttpClient
from perfeng.integration.models import RetryConfig, Snapshot
from perfeng.integration.protocols import HttpClient, MetadataMapper

logger = logging.getLogger(__name__)


class StorageRunRepository:
    """Persists performance run metadata via REST API."""

    def __init__(
        self,
        base_url: str,
        mapper: MetadataMapper,
        http_client: HttpClient | None = None,
        retry: RetryConfig | None = None,
    ):
        self._mapper = mapper
        self._client = ResilientHttpClient(base_url, client=http_client, retry=retry)
        self._logger = logging.getLogger(__name__)

    async def save(self, metadata: PerformanceRunMetadata) -> dict[str, Any]:
        run_payload = self._mapper.map_run(metadata)
        environment_payload = self._mapper.map_environment(metadata)

        payload = run_payload.model_dump()
        if environment_payload:
            payload["environment"] = environment_payload.model_dump()

        self._logger.debug("Persisting run metadata: suite=%s", metadata.run.suite)
        result = await self._client.post("/api/v1/runs/", json=payload)
        self._logger.info("Persisted run metadata for suite=%s", metadata.run.suite)
        return result

    async def close(self) -> None:
        await self._client.close()


class StorageSnapshotRepository:
    """Persists resource snapshots via REST API."""

    def __init__(
        self,
        base_url: str,
        http_client: HttpClient | None = None,
        retry: RetryConfig | None = None,
    ):
        self._client = ResilientHttpClient(base_url, client=http_client, retry=retry)
        self._logger = logging.getLogger(__name__)

    async def post_snapshots(self, run_id: str, snapshots: list[Snapshot]) -> None:
        for snapshot in snapshots:
            payload = {
                "resource_type": snapshot.resource_type,
                "value_current": snapshot.value_current,
                "unit": snapshot.unit,
                "test_phase": snapshot.test_phase,
                "attributes": snapshot.attributes,
            }
            await self._client.post(f"/api/v1/runs/{run_id}/snapshots/", json=payload)
        self._logger.debug("Posted %d snapshots for run %s", len(snapshots), run_id)

    async def close(self) -> None:
        await self._client.close()
