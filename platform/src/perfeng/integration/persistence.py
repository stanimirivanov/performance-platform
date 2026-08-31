"""Facade for persisting performance run metadata."""

from __future__ import annotations

from typing import Any

from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.integration.mappers import DefaultMetadataMapper
from perfeng.integration.protocols import HttpClient
from perfeng.integration.repositories import StorageRunRepository


class MetadataPersistenceClient:
    """High-level client for metadata persistence."""

    def __init__(
        self,
        base_url: str,
        client: HttpClient | None = None,
    ):
        self._repository = StorageRunRepository(
            base_url=base_url,
            mapper=DefaultMetadataMapper(),
            http_client=client,
        )

    async def save(self, metadata: PerformanceRunMetadata) -> dict[str, Any]:
        """Persist the metadata and return the API response JSON."""
        return await self._repository.save(metadata)

    async def close(self) -> None:
        await self._repository.close()

    async def __aenter__(self) -> MetadataPersistenceClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
