"""Resource snapshot routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage import SnapshotCreate, SnapshotRepository, SnapshotService, get_session

router = APIRouter(prefix="/api/v1/runs/{run_id}/snapshots", tags=["snapshots"])


def get_snapshot_service(session: AsyncSession = Depends(get_session)) -> SnapshotService:
    """Dependency injection for SnapshotService."""
    repo = SnapshotRepository(session)
    return SnapshotService(repo)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    run_id: UUID,
    snapshot_data: SnapshotCreate,
    service: SnapshotService = Depends(get_snapshot_service),
):
    """Add a resource snapshot for a run."""
    result = await service.create_snapshot(run_id, snapshot_data)
    return result


@router.get("/")
async def list_snapshots(
    run_id: UUID,
    resource_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: SnapshotService = Depends(get_snapshot_service),
):
    """List snapshots for a run."""
    snapshots = await service.list_snapshots(run_id, resource_type, limit, offset)
    return snapshots
