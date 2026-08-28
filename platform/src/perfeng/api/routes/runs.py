"""Run routes."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from perfeng.api.dependencies import RunServiceDep
from perfeng.storage.schemas import (
    EnvironmentCreate,
    RunCreate,
    RunCreateResponse,
    RunResponse,
    RunUpdate,
)

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.post("/", response_model=RunCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    run_data: RunCreate,
    service: RunServiceDep,
    environment: EnvironmentCreate | None = None,
):
    return await service.create_run(run_data, environment)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: UUID, service: RunServiceDep):
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.patch("/{run_id}", response_model=RunResponse)
async def update_run(run_id: UUID, update_data: RunUpdate, service: RunServiceDep):
    updated = await service.update_run(run_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Run not found")
    return updated


@router.get("/", response_model=list[RunResponse])
async def list_runs(
    service: RunServiceDep,
    status: Annotated[str | None, Query()] = None,
    test_name: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    fingerprint: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return await service.list_runs(
        status, test_name, start_date, end_date, fingerprint, limit, offset
    )
