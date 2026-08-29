"""Pydantic schemas for runs."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from perfeng.storage.schemas.environment import EnvironmentResponse


class RunCreate(BaseModel):
    """Payload for creating a run."""

    test_name: str
    test_script: str | None = None
    test_profile: str | None = None
    status: str = "pending"
    thresholds: dict[str, Any] | None = None
    parameters: dict[str, Any] | None = None
    tags: list[str] | None = None
    triggered_by: str | None = None
    trigger_type: str = "manual"
    ci_build_id: str | None = None
    ci_job_id: str | None = None
    policy_version: str | None = None
    notes: str | None = None


class RunUpdate(BaseModel):
    """Payload for updating a run."""

    status: str | None = None
    end_time: datetime | None = None
    duration_seconds: int | None = None
    success_rate: float | None = None
    average_response_time_ms: float | None = None
    percentiles: dict[str, float] | None = None
    error_count: int | None = None
    total_requests: int | None = None


class RunResponse(BaseModel):
    """Response model for a run."""

    model_config = ConfigDict(from_attributes=True)
    run_id: UUID
    test_name: str
    test_script: str | None = None
    test_profile: str | None = None
    status: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_seconds: int | None = None
    thresholds: dict[str, Any] | None = None
    parameters: dict[str, Any] | None = None
    tags: list[str] | None = None
    triggered_by: str | None = None
    trigger_type: str | None = None
    ci_build_id: str | None = None
    ci_job_id: str | None = None
    policy_version: str | None = None
    notes: str | None = None
    success_rate: float | None = None
    average_response_time_ms: float | None = None
    percentiles: dict[str, float] | None = None
    error_count: int | None = None
    total_requests: int | None = None
    created_at: datetime
    updated_at: datetime
    environment: EnvironmentResponse | None = None


class RunCreateResponse(BaseModel):
    """Response model for a create run."""

    run_id: UUID
    environment_id: UUID | None = None


class RunFilter(BaseModel):
    """Query parameters for listing runs."""

    status: str | None = None
    test_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    fingerprint: str | None = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
