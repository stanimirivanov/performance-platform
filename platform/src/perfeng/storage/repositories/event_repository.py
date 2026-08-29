"""Correlation event repository (stateless)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.generated_models import CorrelationEvents
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import EventCreate


class EventRepository(BaseRepository[CorrelationEvents, EventCreate]):
    """Repository for CorrelationEvent operations."""

    def __init__(self):
        super().__init__(CorrelationEvents)

    async def create_for_run(
        self,
        session: AsyncSession,
        run_id: UUID,
        event_data: EventCreate,
    ) -> CorrelationEvents:
        """Create an event for a specific run."""

        event = CorrelationEvents(run_id=run_id, **event_data.model_dump())
        session.add(event)
        await session.flush()
        return event

    async def list_by_run(
        self,
        session: AsyncSession,
        run_id: UUID,
        event_type: str | None = None,
        phase_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CorrelationEvents]:
        """List events for a run with optional filters."""

        query = select(CorrelationEvents).where(CorrelationEvents.run_id == run_id)
        if event_type:
            query = query.where(CorrelationEvents.event_type == event_type)
        if phase_name:
            query = query.where(CorrelationEvents.phase_name == phase_name)
        query = query.order_by(CorrelationEvents.event_time.asc()).limit(limit).offset(offset)
        result = await session.execute(query)
        return list(result.scalars().all())
