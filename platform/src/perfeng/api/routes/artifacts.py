"""Data artifact routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.api.dependencies import get_artifact_service
from perfeng.storage.database import get_session
from perfeng.storage.schemas import ArtifactCreate, ArtifactFilter, ArtifactResponse
from perfeng.storage.services import ArtifactService

router = APIRouter(prefix="/api/v1/runs/{run_id}/artifacts", tags=["artifacts"])


@router.post("/", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    run_id: UUID,
    artifact_data: ArtifactCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[ArtifactService, Depends(get_artifact_service)],
):
    """Add a data artifact for a run."""
    return await service.create_artifact(session, run_id, artifact_data)


@router.get("/", response_model=list[ArtifactResponse])
async def list_artifacts(
    run_id: UUID,
    filters: Annotated[ArtifactFilter, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[ArtifactService, Depends(get_artifact_service)],
):
    """List artifacts for a run."""
    return await service.list_artifacts(session, run_id, filters)
