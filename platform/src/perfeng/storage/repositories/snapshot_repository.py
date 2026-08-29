"""Resource snapshot repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.generated_models import ResourceSnapshots
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import SnapshotCreate, SnapshotFilter


class SnapshotRepository(BaseRepository[ResourceSnapshots, SnapshotCreate]):
    """Repository for ResourceSnapshot operations."""

    def __init__(self):
        super().__init__(ResourceSnapshots)

    async def create_for_run(
        self,
        session: AsyncSession,
        run_id: UUID,
        snapshot_data: SnapshotCreate,
    ) -> ResourceSnapshots:
        """Create a snapshot for a specific run."""

        snapshot = ResourceSnapshots(run_id=run_id, **snapshot_data.model_dump())
        session.add(snapshot)
        await session.flush()
        return snapshot

    async def list_by_run(
        self,
        session: AsyncSession,
        run_id: UUID,
        filters: SnapshotFilter,
    ) -> list[ResourceSnapshots]:
        """List snapshots for a run with optional filter."""

        query = select(ResourceSnapshots).where(ResourceSnapshots.run_id == run_id)

        query = self.apply_filters(
            query,
            ResourceSnapshots.resource_type == filters.resource_type
            if filters.resource_type
            else None,
        )

        query = (
            query.order_by(ResourceSnapshots.snapshot_time.asc())
            .limit(filters.limit)
            .offset(filters.offset)
        )
        result = await session.execute(query)
        return list(result.scalars().all())
