"""Correlation event repository (stateless)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.generated_models import CorrelationEvents
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import EventCreate, EventFilter


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
        filters: EventFilter,
    ) -> list[CorrelationEvents]:
        """List events for a run with optional filters."""

        query = select(CorrelationEvents).where(CorrelationEvents.run_id == run_id)

        query = self.apply_filters(
            query,
            CorrelationEvents.event_type == filters.event_type if filters.event_type else None,
            CorrelationEvents.phase_name == filters.phase_name if filters.phase_name else None,
        )

        query = (
            query.order_by(CorrelationEvents.event_time.asc())
            .limit(filters.limit)
            .offset(filters.offset)
        )
        result = await session.execute(query)
        return list(result.scalars().all())
