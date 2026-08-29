"""Run routes."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi_class import View
from fastapi_injector import Injected

from perfeng.storage.schemas import (
    EnvironmentCreate,
    RunCreate,
    RunCreateResponse,
    RunResponse,
    RunUpdate,
)
from perfeng.storage.services.run_service import RunService

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@View(router)
class RunView:
    service: RunService = Injected(RunService)

    @router.post("/", response_model=RunCreateResponse, status_code=status.HTTP_201_CREATED)
    async def create_run(
        self,
        run_data: RunCreate,
        environment: EnvironmentCreate | None = None,
    ):
        return await self.service.create_run(run_data, environment)

    @router.get("/{run_id}", response_model=RunResponse)
    async def get_run(self, run_id: UUID):
        run = await self.service.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    @router.patch("/{run_id}", response_model=RunResponse)
    async def update_run(self, run_id: UUID, update_data: RunUpdate):
        updated = await self.service.update_run(run_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Run not found")
        return updated

    @router.get("/", response_model=list[RunResponse])
    async def list_runs(
        self,
        status: Annotated[str | None, Query()] = None,
        test_name: Annotated[str | None, Query()] = None,
        start_date: Annotated[datetime | None, Query()] = None,
        end_date: Annotated[datetime | None, Query()] = None,
        fingerprint: Annotated[str | None, Query()] = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        return await self.service.list_runs(
            status, test_name, start_date, end_date, fingerprint, limit, offset
        )
