"""Data artifact routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi_class import View
from fastapi_injector import Injected
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.database import get_session
from perfeng.storage.schemas import ArtifactCreate, ArtifactFilter, ArtifactResponse
from perfeng.storage.services import ArtifactService

router = APIRouter(prefix="/api/v1/runs/{run_id}/artifacts", tags=["artifacts"])


@View(router)
class RunView:
    service: ArtifactService = Injected(ArtifactService)

    @router.post("/", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
    async def create_artifact(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        run_id: UUID,
        artifact_data: ArtifactCreate,
    ):
        """Add a data artifact for a run."""

        return await self.service.create_artifact(session, run_id, artifact_data)

    @router.get("/", response_model=list[ArtifactResponse])
    async def list_artifacts(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        run_id: UUID,
        filters: Annotated[ArtifactFilter, Depends()],
    ):
        """List artifacts for a run."""

        return await self.service.list_artifacts(session, run_id, filters)
