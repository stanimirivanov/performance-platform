"""Pydantic schemas for snapshots."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SnapshotCreate(BaseModel):
    """Payload for creating a snapshot."""

    resource_type: str
    node_name: str | None = None
    namespace: str | None = None
    pod_name: str | None = None
    container_name: str | None = None
    value_min: float | None = None
    value_max: float | None = None
    value_avg: float | None = None
    value_current: float | None = None
    unit: str | None = None
    test_phase: str | None = None
    time_elapsed_seconds: int | None = None
    metadata: dict[str, Any] | None = None


class SnapshotResponse(BaseModel):
    """Response model for a snapshot."""

    model_config = ConfigDict(from_attributes=True)
    snapshot_id: UUID
    run_id: UUID
    resource_type: str
    node_name: str | None = None
    namespace: str | None = None
    pod_name: str | None = None
    container_name: str | None = None
    value_min: float | None = None
    value_max: float | None = None
    value_avg: float | None = None
    value_current: float | None = None
    unit: str | None = None
    snapshot_time: datetime
    test_phase: str | None = None
    time_elapsed_seconds: int | None = None
    metadata: dict[str, Any] | None = None


class SnapshotFilter(BaseModel):
    """Query parameters for listing snapshots."""

    resource_type: str | None = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
