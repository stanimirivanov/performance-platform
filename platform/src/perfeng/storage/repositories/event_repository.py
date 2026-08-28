"""Correlation event repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.models import CorrelationEvent
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import EventCreate


class EventRepository(BaseRepository[CorrelationEvent, EventCreate]):
    """Repository for CorrelationEvent operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CorrelationEvent, session)

    async def create_for_run(self, run_id: UUID, event_data: EventCreate) -> CorrelationEvent:
        """Create an event for a specific run."""
        event = CorrelationEvent(run_id=run_id, **event_data.model_dump())
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_by_run(
        self,
        run_id: UUID,
        event_type: str | None = None,
        phase_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CorrelationEvent]:
        """List events for a run with optional filters."""
        query = select(CorrelationEvent).where(CorrelationEvent.run_id == run_id)
        if event_type:
            query = query.where(CorrelationEvent.event_type == event_type)
        if phase_name:
            query = query.where(CorrelationEvent.phase_name == phase_name)
        query = query.order_by(CorrelationEvent.event_time.asc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
