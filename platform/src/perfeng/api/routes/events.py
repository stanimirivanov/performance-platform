"""Correlation event routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage import EventCreate, EventRepository, EventService, get_session

router = APIRouter(prefix="/api/v1/runs/{run_id}/events", tags=["events"])


def get_event_service(session: AsyncSession = Depends(get_session)) -> EventService:
    """Dependency injection for EventService."""
    repo = EventRepository(session)
    return EventService(repo)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event(
    run_id: UUID,
    event_data: EventCreate,
    service: EventService = Depends(get_event_service),
):
    """Add a correlation event for a run."""
    result = await service.create_event(run_id, event_data)
    return result


@router.get("/")
async def list_events(
    run_id: UUID,
    event_type: str | None = Query(None),
    phase_name: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: EventService = Depends(get_event_service),
):
    """List events for a run."""
    events = await service.list_events(run_id, event_type, phase_name, limit, offset)
    return events
