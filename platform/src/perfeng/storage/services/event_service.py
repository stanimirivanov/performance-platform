"""Event service."""

from uuid import UUID

from perfeng.storage.repositories.event_repository import EventRepository
from perfeng.storage.schemas import EventCreate, EventResponse


class EventService:
    """Service for correlation event operations."""

    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    async def create_event(
        self,
        run_id: UUID,
        event_data: EventCreate,
    ) -> EventResponse:
        """Create a new event for a run."""
        event = await self.event_repo.create_for_run(run_id, event_data)
        return EventResponse.model_validate(event)

    async def list_events(
        self,
        run_id: UUID,
        event_type: str | None = None,
        phase_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventResponse]:
        """List events for a run."""
        events = await self.event_repo.list_by_run(run_id, event_type, phase_name, limit, offset)
        return [EventResponse.model_validate(e) for e in events]
