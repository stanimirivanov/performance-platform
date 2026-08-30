"""Run routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.api.dependencies import get_run_service
from perfeng.storage.database import get_session
from perfeng.storage.schemas import RunCreate, RunCreateResponse, RunFilter, RunResponse, RunUpdate
from perfeng.storage.services import RunService

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.post("/", response_model=RunCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    run_data: RunCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[RunService, Depends(get_run_service)],
):
    """Create a new run (optionally with environment)."""
    return await service.create_run(session, run_data)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[RunService, Depends(get_run_service)],
):
    """Get run by run id."""
    run = await service.get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.patch("/{run_id}", response_model=RunResponse)
async def update_run(
    run_id: UUID,
    update_data: RunUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[RunService, Depends(get_run_service)],
):
    """Update a run."""
    updated = await service.update_run(session, run_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Run not found")
    return updated


@router.get("/", response_model=list[RunResponse])
async def list_runs(
    filters: Annotated[RunFilter, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[RunService, Depends(get_run_service)],
):
    """List runs with filters."""
    return await service.list_runs(session, filters)
