"""Pydantic schemas for correlation events."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    """Payload for creating a correlation event."""

    event_type: str
    phase_name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    attributes: dict[str, Any] | None = None
    sequence_number: int | None = None
    parent_event_id: UUID | None = None


class EventResponse(BaseModel):
    """Response model for a correlation event."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    event_id: UUID
    run_id: UUID
    event_type: str
    phase_name: str | None = None
    event_time: datetime
    description: str | None = None
    tags: list[str] | None = None
    attributes: dict[str, Any] | None
    sequence_number: int | None = None
    parent_event_id: UUID | None = None


class EventFilter(BaseModel):
    """Query parameters for listing correlation events."""

    event_type: str | None = None
    phase_name: str | None = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
