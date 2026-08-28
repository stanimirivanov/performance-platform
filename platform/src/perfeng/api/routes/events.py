"""Correlation event routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from perfeng.api.dependencies import EventServiceDep
from perfeng.storage.schemas import EventCreate, EventResponse

router = APIRouter(prefix="/api/v1/runs/{run_id}/events", tags=["events"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    run_id: UUID,
    event_data: EventCreate,
    service: EventServiceDep,
):
    """Add a correlation event for a run."""
    return await service.create_event(run_id, event_data)


@router.get("/", response_model=list[EventResponse])
async def list_events(
    run_id: UUID,
    service: EventServiceDep,
    event_type: Annotated[str | None, Query()] = None,
    phase_name: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List events for a run."""
    return await service.list_events(run_id, event_type, phase_name, limit, offset)
