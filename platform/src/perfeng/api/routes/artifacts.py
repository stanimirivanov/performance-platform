"""Data artifact routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage import ArtifactCreate, ArtifactRepository, ArtifactService, get_session

router = APIRouter(prefix="/api/v1/runs/{run_id}/artifacts", tags=["artifacts"])


def get_artifact_service(session: AsyncSession = Depends(get_session)) -> ArtifactService:
    """Dependency injection for ArtifactService."""
    repo = ArtifactRepository(session)
    return ArtifactService(repo)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_artifact(
    run_id: UUID,
    artifact_data: ArtifactCreate,
    service: ArtifactService = Depends(get_artifact_service),
):
    """Add a data artifact for a run."""
    result = await service.create_artifact(run_id, artifact_data)
    return result


@router.get("/")
async def list_artifacts(
    run_id: UUID,
    data_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: ArtifactService = Depends(get_artifact_service),
):
    """List artifacts for a run."""
    artifacts = await service.list_artifacts(run_id, data_type, limit, offset)
    return artifacts
