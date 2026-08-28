"""Artifact service."""

from uuid import UUID

from perfeng.storage.repositories.artifact_repository import ArtifactRepository
from perfeng.storage.schemas import ArtifactCreate, ArtifactResponse


class ArtifactService:
    """Service for data artifact operations."""

    def __init__(self, artifact_repo: ArtifactRepository):
        self.artifact_repo = artifact_repo

    async def create_artifact(
        self,
        run_id: UUID,
        artifact_data: ArtifactCreate,
    ) -> ArtifactResponse:
        """Create a new artifact for a run."""
        artifact = await self.artifact_repo.create_for_run(run_id, artifact_data)
        return ArtifactResponse.model_validate(artifact)

    async def list_artifacts(
        self,
        run_id: UUID,
        data_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ArtifactResponse]:
        """List artifacts for a run."""
        artifacts = await self.artifact_repo.list_by_run(run_id, data_type, limit, offset)
        return [ArtifactResponse.model_validate(a) for a in artifacts]
