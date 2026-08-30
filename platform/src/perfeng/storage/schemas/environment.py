"""Pydantic schemas for Environments."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EnvironmentCreate(BaseModel):
    """Payload for creating an environment."""

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
    """Response model for an environment."""

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
