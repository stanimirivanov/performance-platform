"""Artifact service."""

from typing import Any
from uuid import UUID

from ..repositories.artifact_repository import ArtifactRepository
from ..schemas import ArtifactCreate


class ArtifactService:
    """Service for data artifact operations."""

    def __init__(self, artifact_repo: ArtifactRepository):
        self.artifact_repo = artifact_repo

    async def create_artifact(
        self,
        run_id: UUID,
        artifact_data: ArtifactCreate,
    ) -> dict[str, Any]:
        """Create a new artifact for a run."""
        artifact = await self.artifact_repo.create_for_run(run_id, artifact_data)
        return {"artifact_id": artifact.artifact_id}

    async def list_artifacts(
        self,
        run_id: UUID,
        data_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DataArtifact]:
        """List artifacts for a run."""
        return await self.artifact_repo.list_by_run(run_id, data_type, limit, offset)
