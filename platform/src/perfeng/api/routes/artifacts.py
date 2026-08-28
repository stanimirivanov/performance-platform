"""Data artifact routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from perfeng.api.dependencies import ArtifactServiceDep
from perfeng.storage.schemas import ArtifactCreate, ArtifactResponse

router = APIRouter(prefix="/api/v1/runs/{run_id}/artifacts", tags=["artifacts"])


@router.post("/", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    run_id: UUID,
    artifact_data: ArtifactCreate,
    service: ArtifactServiceDep,
):
    """Add a data artifact for a run."""
    return await service.create_artifact(run_id, artifact_data)


@router.get("/", response_model=list[ArtifactResponse])
async def list_artifacts(
    run_id: UUID,
    service: ArtifactServiceDep,
    data_type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List artifacts for a run."""
    return await service.list_artifacts(run_id, data_type, limit, offset)
