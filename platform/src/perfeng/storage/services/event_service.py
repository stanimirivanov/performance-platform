"""Event service."""

from uuid import UUID

from injector import inject
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.repositories import EventRepository
from perfeng.storage.schemas import EventCreate, EventFilter, EventResponse


class EventService:
    """Service for correlation event operations."""

    @inject
    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    async def create_event(
        self,
        session: AsyncSession,
        run_id: UUID,
        event_data: EventCreate,
    ) -> EventResponse:
        """Create a new event for a run."""

        event = await self.event_repo.create_for_run(session, run_id, event_data)
        return EventResponse.model_validate(event)

    async def list_events(
        self,
        session: AsyncSession,
        run_id: UUID,
        filters: EventFilter,
    ) -> list[EventResponse]:
        """List events for a run."""

        events = await self.event_repo.list_by_run(session, run_id, filters)
        return [EventResponse.model_validate(e) for e in events]
