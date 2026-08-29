"""Run routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_class import View
from fastapi_injector import Injected
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.database import get_session
from perfeng.storage.schemas import (
    EnvironmentCreate,
    RunCreate,
    RunCreateResponse,
    RunFilter,
    RunResponse,
    RunUpdate,
)
from perfeng.storage.services import RunService

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@View(router)
class RunView:
    service: RunService = Injected(RunService)

    @router.post("/", response_model=RunCreateResponse, status_code=status.HTTP_201_CREATED)
    async def create_run(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        run_data: RunCreate,
        environment: EnvironmentCreate | None = None,
    ):
        """Create a new run with optional environment."""

        return await self.service.create_run(session, run_data, environment)

    @router.get("/{run_id}", response_model=RunResponse)
    async def get_run(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        run_id: UUID,
    ):
        """Get run by run id."""

        run = await self.service.get_run(session, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    @router.patch("/{run_id}", response_model=RunResponse)
    async def update_run(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        run_id: UUID,
        update_data: RunUpdate,
    ):
        """Update a run."""

        updated = await self.service.update_run(session, run_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Run not found")
        return updated

    @router.get("/", response_model=list[RunResponse])
    async def list_runs(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        filters: Annotated[RunFilter, Depends()],
    ):
        """List runs with filters."""
        return await self.service.list_runs(session, filters)
