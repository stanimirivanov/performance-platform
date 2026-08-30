"""Resource snapshot routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.api.dependencies import get_snapshot_service
from perfeng.storage.database import get_session
from perfeng.storage.schemas import SnapshotCreate, SnapshotFilter, SnapshotResponse
from perfeng.storage.services import SnapshotService

router = APIRouter(prefix="/api/v1/runs/{run_id}/snapshots", tags=["snapshots"])


@router.post("/", response_model=SnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    run_id: UUID,
    snapshot_data: SnapshotCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
):
    """Add a resource snapshot for a run."""
    return await service.create_snapshot(session, run_id, snapshot_data)


@router.get("/", response_model=list[SnapshotResponse])
async def list_snapshots(
    run_id: UUID,
    filters: Annotated[SnapshotFilter, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
):
    """List snapshots for a run."""
    return await service.list_snapshots(session, run_id, filters)
