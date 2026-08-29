"""Resource snapshot routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi_class import View
from fastapi_injector import Injected

from perfeng.storage.schemas import SnapshotCreate, SnapshotResponse
from perfeng.storage.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/v1/runs/{run_id}/snapshots", tags=["snapshots"])


@View(router)
class RunView:
    service: SnapshotService = Injected(SnapshotService)

    @router.post("/", response_model=SnapshotResponse, status_code=status.HTTP_201_CREATED)
    async def create_snapshot(
        self,
        run_id: UUID,
        snapshot_data: SnapshotCreate,
    ):
        """Add a resource snapshot for a run."""
        return await self.service.create_snapshot(run_id, snapshot_data)

    @router.get("/", response_model=list[SnapshotResponse])
    async def list_snapshots(
        self,
        run_id: UUID,
        resource_type: Annotated[str | None, Query()] = None,
        limit: Annotated[int, Query(ge=1, le=1000)] = 100,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        """List snapshots for a run."""
        return await self.service.list_snapshots(run_id, resource_type, limit, offset)
