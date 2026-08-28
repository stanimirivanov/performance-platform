"""Data artifact repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DataArtifact
from ..schemas import ArtifactCreate
from .base import BaseRepository


class ArtifactRepository(BaseRepository[DataArtifact, ArtifactCreate, None]):
    """Repository for DataArtifact operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(DataArtifact, session)
        self.model.id = DataArtifact.artifact_id  # type: ignore

    async def create_for_run(self, run_id: UUID, artifact_data: ArtifactCreate) -> DataArtifact:
        """Create an artifact for a specific run."""
        artifact = DataArtifact(run_id=run_id, **artifact_data.model_dump())
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    async def list_by_run(
        self,
        run_id: UUID,
        data_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DataArtifact]:
        """List artifacts for a run with optional filter."""
        query = select(DataArtifact).where(DataArtifact.run_id == run_id)
        if data_type:
            query = query.where(DataArtifact.data_type == data_type)
        query = query.order_by(DataArtifact.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
