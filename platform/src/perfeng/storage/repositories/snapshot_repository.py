"""Resource snapshot repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ResourceSnapshot
from ..schemas import SnapshotCreate
from .base import BaseRepository


class SnapshotRepository(BaseRepository[ResourceSnapshot, SnapshotCreate, None]):
    """Repository for ResourceSnapshot operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ResourceSnapshot, session)
        self.model.id = ResourceSnapshot.snapshot_id  # type: ignore

    async def create_for_run(self, run_id: UUID, snapshot_data: SnapshotCreate) -> ResourceSnapshot:
        """Create a snapshot for a specific run."""
        snapshot = ResourceSnapshot(run_id=run_id, **snapshot_data.model_dump())
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def list_by_run(
        self,
        run_id: UUID,
        resource_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ResourceSnapshot]:
        """List snapshots for a run with optional filter."""
        query = select(ResourceSnapshot).where(ResourceSnapshot.run_id == run_id)
        if resource_type:
            query = query.where(ResourceSnapshot.resource_type == resource_type)
        query = query.order_by(ResourceSnapshot.snapshot_time.asc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
