"""Data artifact repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.models import DataArtifacts
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import ArtifactCreate, ArtifactFilter


class ArtifactRepository(BaseRepository[DataArtifacts, ArtifactCreate]):
    """Repository for DataArtifact operations."""

    def __init__(self):
        super().__init__(DataArtifacts)

    async def create_for_run(
        self,
        session: AsyncSession,
        run_id: UUID,
        artifact_data: ArtifactCreate,
    ) -> DataArtifacts:
        """Create an artifact for a specific run."""

        artifact = DataArtifacts(run_id=run_id, **artifact_data.model_dump())
        session.add(artifact)
        await session.flush()
        return artifact

    async def list_by_run(
        self,
        session: AsyncSession,
        run_id: UUID,
        filters: ArtifactFilter,
    ) -> list[DataArtifacts]:
        """List artifacts for a run with optional filter."""

        query = select(DataArtifacts).where(DataArtifacts.run_id == run_id)

        query = self.apply_filters(
            query,
            DataArtifacts.data_type == filters.data_type if filters.data_type else None,
        )

        query = (
            query.order_by(DataArtifacts.created_at.desc())
            .limit(filters.limit)
            .offset(filters.offset)
        )
        result = await session.execute(query)
        return list(result.scalars().all())
