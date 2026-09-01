"""Abstract contracts for the integration layer."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.integration.models import Snapshot
from perfeng.storage.schemas import EnvironmentCreate, RunCreate


@runtime_checkable
class HttpClient(Protocol):
    """Async HTTP client abstraction."""

    async def post(
        self,
        url: str,
        json: dict[str, Any],
        timeout: float | None = None,
    ) -> Any:  # <-- now Any; concrete impls return httpx.Response
        """POST JSON payload and return the raw response object."""
        ...

    async def close(self) -> None:
        """Release underlying connections."""
        ...


@runtime_checkable
class MetadataMapper(Protocol):
    """Maps domain metadata to storage DTOs."""

    def map_run(self, metadata: PerformanceRunMetadata) -> RunCreate: ...
    def map_environment(self, metadata: PerformanceRunMetadata) -> EnvironmentCreate | None: ...


@runtime_checkable
class MetricCollector(Protocol):
    """Collects system resource snapshots."""

    def collect(self) -> list[Snapshot]: ...


@runtime_checkable
class RunRepository(Protocol):
    """Persists performance run metadata."""

    async def save(self, metadata: PerformanceRunMetadata) -> dict[str, Any]: ...


@runtime_checkable
class SnapshotRepository(Protocol):
    """Persists resource snapshots."""

    async def post_snapshots(self, run_id: str, snapshots: list[Snapshot]) -> None: ...
