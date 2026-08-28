"""Routes for run operations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...storage import RunCreate, RunService, RunUpdate
from ..dependencies import get_run_service

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_run(
    run_data: RunCreate,
    service: RunService = Depends(get_run_service),
):
    """Create a new run."""
    result = await service.create_run(run_data)
    return result


@router.get("/{run_id}")
async def get_run(
    run_id: UUID,
    service: RunService = Depends(get_run_service),
):
    """Get a run by ID."""
    run = await service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.patch("/{run_id}")
async def update_run(
    run_id: UUID,
    update_data: RunUpdate,
    service: RunService = Depends(get_run_service),
):
    """Update a run."""
    updated = await service.update_run(run_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Run not found")
    return updated


@router.get("/")
async def list_runs(
    status: str | None = Query(None),
    test_name: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    fingerprint: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: RunService = Depends(get_run_service),
):
    """List runs with filters."""
    return await service.list_runs(
        status, test_name, start_date, end_date, fingerprint, limit, offset
    )
