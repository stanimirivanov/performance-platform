"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

# === Run schemas ===


class RunCreate(BaseModel):
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
    status: str | None = None
    end_time: datetime | None = None
    duration_seconds: int | None = None
    success_rate: float | None = None
    average_response_time_ms: float | None = None
    percentiles: dict[str, float] | None = None
    error_count: int | None = None
    total_requests: int | None = None


class RunResponse(BaseModel):
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
    environment: Optional["EnvironmentResponse"] = None
