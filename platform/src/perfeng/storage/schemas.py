"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# === Environment schemas ===


class EnvironmentCreate(BaseModel):
    cluster_name: str | None = None
    cluster_type: str | None = None
    kubernetes_version: str | None = None
    cloud_provider: str | None = None
    cloud_region: str | None = None
    cloud_zone: str | None = None
    node_count: int | None = None
    node_os: str | None = None
    node_kernel: str | None = None
    node_architecture: str | None = None
    node_resource_capacity: dict[str, Any] | None = None
    fingerprint_hash: str


class EnvironmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    environment_id: UUID
    run_id: UUID
    cluster_name: str | None = None
    cluster_type: str | None = None
    kubernetes_version: str | None = None
    cloud_provider: str | None = None
    cloud_region: str | None = None
    cloud_zone: str | None = None
    node_count: int | None = None
    node_os: str | None = None
    node_kernel: str | None = None
    node_architecture: str | None = None
    node_resource_capacity: dict[str, Any] | None = None
    fingerprint_hash: str
    created_at: datetime


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
    run_id: UUID
    environment_id: UUID | None = None


# === Snapshot schemas ===


class SnapshotCreate(BaseModel):
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


# === Event schemas ===


class EventCreate(BaseModel):
    event_type: str
    phase_name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    sequence_number: int | None = None
    parent_event_id: UUID | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: UUID
    run_id: UUID
    event_type: str
    phase_name: str | None = None
    event_time: datetime
    description: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    sequence_number: int | None = None
    parent_event_id: UUID | None = None


# === Artifact schemas ===


class ArtifactCreate(BaseModel):
    artifact_type: str
    data_type: str  # 'baseline', 'current', etc.
    storage_path: str | None = None
    storage_uri: str | None = None
    storage_backend: str | None = "local"
    data_size_bytes: int | None = None
    checksum: str | None = None
    file_format: str | None = None
    description: str | None = None
    tags: list[str] | None = None


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    artifact_id: UUID
    run_id: UUID
    artifact_type: str
    data_type: str
    storage_path: str | None = None
    storage_uri: str | None = None
    storage_backend: str | None = None
    data_size_bytes: int | None = None
    checksum: str | None = None
    file_format: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    created_at: datetime
