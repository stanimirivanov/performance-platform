"""Event service."""

from typing import Any
from uuid import UUID

from ..repositories.event_repository import EventRepository
from ..schemas import EventCreate


class EventService:
    """Service for correlation event operations."""

    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    async def create_event(
        self,
        run_id: UUID,
        event_data: EventCreate,
    ) -> dict[str, Any]:
        """Create a new event for a run."""
        event = await self.event_repo.create_for_run(run_id, event_data)
        return {"event_id": event.event_id}

    async def list_events(
        self,
        run_id: UUID,
        event_type: str | None = None,
        phase_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CorrelationEvent]:
        """List events for a run."""
        return await self.event_repo.list_by_run(run_id, event_type, phase_name, limit, offset)
