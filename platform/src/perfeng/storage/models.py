"""SQLAlchemy ORM models for metadata storage."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TestRun(Base):
    __tablename__ = "test_runs"
    __table_args__ = {"schema": "metadata"}

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_script: Mapped[str | None] = mapped_column(String(500))
    test_profile: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    thresholds: Mapped[dict | None] = mapped_column(JSON)
    parameters: Mapped[dict | None] = mapped_column(JSON)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    triggered_by: Mapped[str | None] = mapped_column(String(100))
    trigger_type: Mapped[str | None] = mapped_column(String(50))
    ci_build_id: Mapped[str | None] = mapped_column(String(255))
    ci_job_id: Mapped[str | None] = mapped_column(String(255))
    policy_version: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    success_rate: Mapped[float | None] = mapped_column(Float)
    average_response_time_ms: Mapped[float | None] = mapped_column(Float)
    percentiles: Mapped[dict | None] = mapped_column(JSON)
    error_count: Mapped[int | None] = mapped_column(Integer, default=0)
    total_requests: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    environment: Mapped["Environment"] = relationship(back_populates="run", uselist=False)
    snapshots: Mapped[list["ResourceSnapshot"]] = relationship(back_populates="run")
    events: Mapped[list["CorrelationEvent"]] = relationship(back_populates="run")
    artifacts: Mapped[list["DataArtifact"]] = relationship(back_populates="run")

    __table_args__ = (
        Index("idx_test_runs_status", "status"),
        Index("idx_test_runs_start_time", "start_time"),
        Index("idx_test_runs_created_at", "created_at"),
        Index("idx_test_runs_status_start_time", "status", "start_time"),
    )


class Environment(Base):
    __tablename__ = "environments"
    __table_args__ = {"schema": "metadata"}

    environment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("metadata.test_runs.run_id", ondelete="CASCADE")
    )
    cluster_name: Mapped[str | None] = mapped_column(String(255))
    cluster_type: Mapped[str | None] = mapped_column(String(50))
    kubernetes_version: Mapped[str | None] = mapped_column(String(50))
    cloud_provider: Mapped[str | None] = mapped_column(String(50))
    cloud_region: Mapped[str | None] = mapped_column(String(50))
    cloud_zone: Mapped[str | None] = mapped_column(String(50))
    node_count: Mapped[int | None] = mapped_column(Integer)
    node_os: Mapped[str | None] = mapped_column(String(100))
    node_kernel: Mapped[str | None] = mapped_column(String(100))
    node_architecture: Mapped[str | None] = mapped_column(String(50))
    node_resource_capacity: Mapped[dict | None] = mapped_column(JSON)
    fingerprint_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    run: Mapped["TestRun"] = relationship(back_populates="environment")

    __table_args__ = (
        Index("idx_environments_fingerprint", "fingerprint_hash"),
        Index("idx_environments_run_id", "run_id"),
        Index("idx_environments_fingerprint_run", "fingerprint_hash", "run_id"),
    )


class ResourceSnapshot(Base):
    __tablename__ = "resource_snapshots"
    __table_args__ = {"schema": "metadata"}

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("metadata.test_runs.run_id", ondelete="CASCADE")
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    node_name: Mapped[str | None] = mapped_column(String(255))
    namespace: Mapped[str | None] = mapped_column(String(255))
    pod_name: Mapped[str | None] = mapped_column(String(255))
    container_name: Mapped[str | None] = mapped_column(String(255))
    value_min: Mapped[float | None] = mapped_column(Float)
    value_max: Mapped[float | None] = mapped_column(Float)
    value_avg: Mapped[float | None] = mapped_column(Float)
    value_current: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(20))
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    test_phase: Mapped[str | None] = mapped_column(String(50))
    time_elapsed_seconds: Mapped[int | None] = mapped_column(Integer)
    metadata: Mapped[dict | None] = mapped_column(JSON)

    run: Mapped["TestRun"] = relationship(back_populates="snapshots")

    __table_args__ = (
        Index("idx_resource_snapshots_run_time", "run_id", "snapshot_time"),
        Index("idx_resource_snapshots_type", "resource_type"),
        Index("idx_resource_snapshots_test_phase", "test_phase", "snapshot_time"),
    )
