"""Snapshot service."""

from uuid import UUID

from injector import inject
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.repositories.snapshot_repository import SnapshotRepository
from perfeng.storage.schemas import SnapshotCreate, SnapshotFilter, SnapshotResponse


class SnapshotService:
    """Service for resource snapshot operations."""

    @inject
    def __init__(self, snapshot_repo: SnapshotRepository):
        self.snapshot_repo = snapshot_repo

    async def create_snapshot(
        self,
        session: AsyncSession,
        run_id: UUID,
        snapshot_data: SnapshotCreate,
    ) -> SnapshotResponse:
        """Create a new snapshot for a run."""

        snapshot = await self.snapshot_repo.create_for_run(session, run_id, snapshot_data)
        return SnapshotResponse.model_validate(snapshot)

    async def list_snapshots(
        self,
        session: AsyncSession,
        run_id: UUID,
        filters: SnapshotFilter,
    ) -> list[SnapshotResponse]:
        """List snapshots for a run."""

        snapshots = await self.snapshot_repo.list_by_run(
            session, run_id, filters.resource_type, filters.limit, filters.offset
        )
        return [SnapshotResponse.model_validate(s) for s in snapshots]
