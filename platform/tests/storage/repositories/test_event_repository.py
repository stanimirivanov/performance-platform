"""Integration tests for EventRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.repositories import EventRepository, RunRepository
from perfeng.storage.schemas import EventCreate, EventFilter, RunCreate


@pytest.mark.asyncio
async def test_create_event(db_session: AsyncSession):
    run_repo = RunRepository()
    event_repo = EventRepository()

    run = await run_repo.create(db_session, RunCreate(test_name="event-run", status="running"))

    event_data = EventCreate(event_type="phase_start", phase_name="warmup")
    event = await event_repo.create_for_run(db_session, run.run_id, event_data)

    assert event.event_id is not None
    assert event.run_id == run.run_id
    assert event.event_type == "phase_start"
    assert event.phase_name == "warmup"


@pytest.mark.asyncio
async def test_list_events_by_type(db_session: AsyncSession):
    run_repo = RunRepository()
    event_repo = EventRepository()

    run = await run_repo.create(db_session, RunCreate(test_name="list-events", status="running"))

    await event_repo.create_for_run(
        db_session, run.run_id, EventCreate(event_type="start", phase_name="setup")
    )
    await event_repo.create_for_run(
        db_session, run.run_id, EventCreate(event_type="end", phase_name="cooldown")
    )

    filters = EventFilter(event_type="start", limit=10, offset=0)
    events = await event_repo.list_by_run(db_session, run.run_id, filters)
    assert len(events) == 1
    assert events[0].event_type == "start"
