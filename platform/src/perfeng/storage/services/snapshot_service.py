"""Snapshot service."""

from typing import Any
from uuid import UUID

from ..repositories.snapshot_repository import SnapshotRepository
from ..schemas import SnapshotCreate


class SnapshotService:
    """Service for resource snapshot operations."""

    def __init__(self, snapshot_repo: SnapshotRepository):
        self.snapshot_repo = snapshot_repo

    async def create_snapshot(
        self,
        run_id: UUID,
        snapshot_data: SnapshotCreate,
    ) -> dict[str, Any]:
        """Create a new snapshot for a run."""
        snapshot = await self.snapshot_repo.create_for_run(run_id, snapshot_data)
        return {"snapshot_id": snapshot.snapshot_id}

    async def list_snapshots(
        self,
        run_id: UUID,
        resource_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ResourceSnapshot]:
        """List snapshots for a run."""
        return await self.snapshot_repo.list_by_run(run_id, resource_type, limit, offset)
