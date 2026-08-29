"""Correlation event routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi_class import View
from fastapi_injector import Injected
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.database import get_session
from perfeng.storage.schemas import EventCreate, EventResponse
from perfeng.storage.services.event_service import EventService

router = APIRouter(prefix="/api/v1/runs/{run_id}/events", tags=["events"])


@View(router)
class RunView:
    service: EventService = Injected(EventService)

    @router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
    async def create_event(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        run_id: UUID,
        event_data: EventCreate,
    ):
        """Add a correlation event for a run."""

        return await self.service.create_event(session, run_id, event_data)

    @router.get("/", response_model=list[EventResponse])
    async def list_events(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        run_id: UUID,
        event_type: Annotated[str | None, Query()] = None,
        phase_name: Annotated[str | None, Query()] = None,
        limit: Annotated[int, Query(ge=1, le=1000)] = 100,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        """List events for a run."""

        return await self.service.list_events(
            session, run_id, event_type, phase_name, limit, offset
        )
