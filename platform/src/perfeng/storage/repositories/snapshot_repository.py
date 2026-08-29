"""Resource snapshot repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.generated_models import ResourceSnapshots
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import SnapshotCreate


class SnapshotRepository(BaseRepository[ResourceSnapshots, SnapshotCreate]):
    """Repository for ResourceSnapshot operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ResourceSnapshots, session)

    async def create_for_run(
        self, run_id: UUID, snapshot_data: SnapshotCreate
    ) -> ResourceSnapshots:
        """Create a snapshot for a specific run."""
        snapshot = ResourceSnapshots(run_id=run_id, **snapshot_data.model_dump())
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def list_by_run(
        self,
        run_id: UUID,
        resource_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ResourceSnapshots]:
        """List snapshots for a run with optional filter."""
        query = select(ResourceSnapshots).where(ResourceSnapshots.run_id == run_id)
        if resource_type:
            query = query.where(ResourceSnapshots.resource_type == resource_type)
        query = query.order_by(ResourceSnapshots.snapshot_time.asc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
