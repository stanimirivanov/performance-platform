"""Run routes - HTTP layer that imports services from storage."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage import (
    EnvironmentRepository,
    RunCreate,
    RunRepository,
    RunService,
    RunUpdate,
    get_session,
)

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


def get_run_service(session: AsyncSession = Depends(get_session)) -> RunService:
    """Dependency injection for RunService."""
    run_repo = RunRepository(session)
    env_repo = EnvironmentRepository(session)
    return RunService(run_repo, env_repo)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_run(
    run_data: RunCreate,
    service: RunService = Depends(get_run_service),
):
    """Create a new run."""
    # Optionally include environment data if provided
    # For simplicity, we just create the run; environment can be added separately
    result = await service.create_run(run_data)
    return result


@router.get("/{run_id}")
async def get_run(
    run_id: UUID,
    service: RunService = Depends(get_run_service),
):
    """Get a run by ID with its environment."""
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
    runs = await service.list_runs(
        status, test_name, start_date, end_date, fingerprint, limit, offset
    )
    return runs
