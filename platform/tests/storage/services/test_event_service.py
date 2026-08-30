"""Unit tests for EventService."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.models import CorrelationEvents
from perfeng.storage.repositories.event_repository import EventRepository
from perfeng.storage.schemas import EventCreate, EventFilter, EventResponse
from perfeng.storage.services.event_service import EventService


@pytest.fixture
def mock_event_repo():
    return Mock(spec=EventRepository)


@pytest.fixture
def service(mock_event_repo):
    return EventService(mock_event_repo)


def make_fake_event(**kwargs):
    defaults = {
        "event_id": uuid4(),
        "run_id": uuid4(),
        "event_type": "phase_start",
        "event_time": __import__("datetime").datetime.now(),
    }
    defaults.update(kwargs)
    return CorrelationEvents(**defaults)


@pytest.mark.asyncio
async def test_create_event(service, mock_event_repo):
    session = AsyncMock(spec=AsyncSession)
    run_id = uuid4()
    data = EventCreate(event_type="milestone", phase_name="warmup")
    fake_event = make_fake_event(run_id=run_id)
    mock_event_repo.create_for_run = AsyncMock(return_value=fake_event)

    result = await service.create_event(session, run_id, data)

    mock_event_repo.create_for_run.assert_awaited_once_with(session, run_id, data)
    assert isinstance(result, EventResponse)
    assert result.event_id == fake_event.event_id


@pytest.mark.asyncio
async def test_list_events(service, mock_event_repo):
    session = AsyncMock(spec=AsyncSession)
    run_id = uuid4()
    filters = EventFilter(event_type="start", limit=10, offset=0)
    fake_events = [make_fake_event()]
    mock_event_repo.list_by_run = AsyncMock(return_value=fake_events)

    result = await service.list_events(session, run_id, filters)

    mock_event_repo.list_by_run.assert_awaited_once_with(session, run_id, filters)
    assert len(result) == 1
    assert isinstance(result[0], EventResponse)
