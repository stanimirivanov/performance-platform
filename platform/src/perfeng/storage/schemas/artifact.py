"""Pydantic schemas for artifacts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ArtifactCreate(BaseModel):
    """Payload for creating an artifact."""

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
    """Response model for an artifact."""

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


class ArtifactFilter(BaseModel):
    """Query parameters for listing artifacts."""

    data_type: str | None = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
