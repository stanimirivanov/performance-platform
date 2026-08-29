"""Data artifact repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.generated_models import DataArtifacts
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import ArtifactCreate


class ArtifactRepository(BaseRepository[DataArtifacts, ArtifactCreate]):
    """Repository for DataArtifact operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(DataArtifacts, session)

    async def create_for_run(self, run_id: UUID, artifact_data: ArtifactCreate) -> DataArtifacts:
        """Create an artifact for a specific run."""
        artifact = DataArtifacts(run_id=run_id, **artifact_data.model_dump())
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    async def list_by_run(
        self,
        run_id: UUID,
        data_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DataArtifacts]:
        """List artifacts for a run with optional filter."""
        query = select(DataArtifacts).where(DataArtifacts.run_id == run_id)
        if data_type:
            query = query.where(DataArtifacts.data_type == data_type)
        query = query.order_by(DataArtifacts.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
