"""Snapshot service."""

from uuid import UUID

from perfeng.storage.repositories.snapshot_repository import SnapshotRepository
from perfeng.storage.schemas import SnapshotCreate, SnapshotResponse


class SnapshotService:
    """Service for resource snapshot operations."""

    def __init__(self, snapshot_repo: SnapshotRepository):
        self.snapshot_repo = snapshot_repo

    async def create_snapshot(
        self,
        run_id: UUID,
        snapshot_data: SnapshotCreate,
    ) -> SnapshotResponse:
        """Create a new snapshot for a run."""
        snapshot = await self.snapshot_repo.create_for_run(run_id, snapshot_data)
        return SnapshotResponse.model_validate(snapshot)

    async def list_snapshots(
        self,
        run_id: UUID,
        resource_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SnapshotResponse]:
        """List snapshots for a run."""
        snapshots = await self.snapshot_repo.list_by_run(run_id, resource_type, limit, offset)
        return [SnapshotResponse.model_validate(s) for s in snapshots]
