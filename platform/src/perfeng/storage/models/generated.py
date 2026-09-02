from typing import Optional
import datetime
import enum
import uuid

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Double, Enum, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class DataType(str, enum.Enum):
    BASELINE = 'baseline'
    CURRENT = 'current'
    HISTORICAL = 'historical'
    COMPARISON = 'comparison'


class ResourceType(str, enum.Enum):
    CPU = 'cpu'
    MEMORY = 'memory'
    DISK = 'disk'
    NETWORK = 'network'
    GPU = 'gpu'


class TestPhase(str, enum.Enum):
    __test__ = False
    SETUP = 'setup'
    WARMUP = 'warmup'
    RAMP_UP = 'ramp_up'
    STEADY = 'steady'
    RAMP_DOWN = 'ramp_down'
    COOLDOWN = 'cooldown'


class TestStatus(str, enum.Enum):
    __test__ = False
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    TIMEOUT = 'timeout'


class Migrations(Base):
    __tablename__ = 'migrations'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='migrations_pkey'),
        UniqueConstraint('name', name='migrations_name_key'),
        {'schema': 'metadata'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    applied_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))


class TestRuns(Base):
    __test__ = False
    __tablename__ = 'test_runs'
    __table_args__ = (
        CheckConstraint('duration_seconds >= 0', name='test_runs_duration_seconds_check'),
        PrimaryKeyConstraint('run_id', name='test_runs_pkey'),
        Index('idx_test_runs_created_at', 'created_at'),
        Index('idx_test_runs_start_time', 'start_time'),
        Index('idx_test_runs_status', 'status'),
        Index('idx_test_runs_status_start_time', 'status', 'start_time'),
        {'schema': 'metadata'}
    )

    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    test_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TestStatus] = mapped_column(Enum(TestStatus, values_callable=lambda cls: [member.value for member in cls], name='test_status', schema='metadata'), nullable=False, server_default=text("'pending'::metadata.test_status"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    test_script: Mapped[Optional[str]] = mapped_column(Text)
    test_profile: Mapped[Optional[str]] = mapped_column(Text)
    start_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    thresholds: Mapped[Optional[dict]] = mapped_column(JSONB)
    parameters: Mapped[Optional[dict]] = mapped_column(JSONB)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text()))
    triggered_by: Mapped[Optional[str]] = mapped_column(Text)
    trigger_type: Mapped[Optional[str]] = mapped_column(Text)
    ci_build_id: Mapped[Optional[str]] = mapped_column(Text)
    ci_job_id: Mapped[Optional[str]] = mapped_column(Text)
    success_rate: Mapped[Optional[float]] = mapped_column(Double(53))
    average_response_time_ms: Mapped[Optional[float]] = mapped_column(Double(53))
    percentiles: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_count: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    total_requests: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    policy_version: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    correlation_events: Mapped[list['CorrelationEvents']] = relationship('CorrelationEvents', back_populates='run')
    data_artifacts: Mapped[list['DataArtifacts']] = relationship('DataArtifacts', back_populates='run')
    environments: Mapped['Environments'] = relationship('Environments', uselist=False, back_populates='run')
    resource_snapshots: Mapped[list['ResourceSnapshots']] = relationship('ResourceSnapshots', back_populates='run')


class CorrelationEvents(Base):
    __tablename__ = 'correlation_events'
    __table_args__ = (
        ForeignKeyConstraint(['parent_event_id'], ['metadata.correlation_events.event_id'], name='correlation_events_parent_event_id_fkey'),
        ForeignKeyConstraint(['run_id'], ['metadata.test_runs.run_id'], ondelete='CASCADE', name='correlation_events_run_id_fkey'),
        PrimaryKeyConstraint('event_id', name='correlation_events_pkey'),
        Index('idx_correlation_events_run_time', 'run_id', 'event_time'),
        Index('idx_correlation_events_type_phase', 'event_type', 'phase_name'),
        {'schema': 'metadata'}
    )

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    event_time: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    event_type: Mapped[Optional[str]] = mapped_column(Text)
    phase_name: Mapped[Optional[TestPhase]] = mapped_column(Enum(TestPhase, values_callable=lambda cls: [member.value for member in cls], name='test_phase', schema='metadata'))
    description: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text()))
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB)
    sequence_number: Mapped[Optional[int]] = mapped_column(Integer)
    parent_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    parent_event: Mapped[Optional['CorrelationEvents']] = relationship('CorrelationEvents', remote_side=[event_id], back_populates='parent_event_reverse')
    parent_event_reverse: Mapped[list['CorrelationEvents']] = relationship('CorrelationEvents', remote_side=[parent_event_id], back_populates='parent_event')
    run: Mapped['TestRuns'] = relationship('TestRuns', back_populates='correlation_events')


class DataArtifacts(Base):
    __tablename__ = 'data_artifacts'
    __table_args__ = (
        ForeignKeyConstraint(['run_id'], ['metadata.test_runs.run_id'], ondelete='CASCADE', name='data_artifacts_run_id_fkey'),
        PrimaryKeyConstraint('artifact_id', name='data_artifacts_pkey'),
        Index('idx_data_artifacts_run', 'run_id'),
        Index('idx_data_artifacts_type', 'data_type'),
        {'schema': 'metadata'}
    )

    artifact_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    data_type: Mapped[DataType] = mapped_column(Enum(DataType, values_callable=lambda cls: [member.value for member in cls], name='data_type', schema='metadata'), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    artifact_type: Mapped[Optional[str]] = mapped_column(Text)
    storage_path: Mapped[Optional[str]] = mapped_column(Text)
    storage_uri: Mapped[Optional[str]] = mapped_column(Text)
    storage_backend: Mapped[Optional[str]] = mapped_column(Text)
    data_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    checksum: Mapped[Optional[str]] = mapped_column(Text)
    file_format: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text()))

    run: Mapped['TestRuns'] = relationship('TestRuns', back_populates='data_artifacts')


class Environments(Base):
    __tablename__ = 'environments'
    __table_args__ = (
        ForeignKeyConstraint(['run_id'], ['metadata.test_runs.run_id'], ondelete='CASCADE', name='environments_run_id_fkey'),
        PrimaryKeyConstraint('environment_id', name='environments_pkey'),
        UniqueConstraint('run_id', 'fingerprint_hash', name='environments_run_id_fingerprint_hash_key'),
        UniqueConstraint('run_id', name='unique_run_id'),
        Index('idx_environments_fingerprint', 'fingerprint_hash'),
        Index('idx_environments_fingerprint_run', 'fingerprint_hash', 'run_id'),
        Index('idx_environments_run_id', 'run_id'),
        {'schema': 'metadata'}
    )

    environment_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    fingerprint_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    cluster_name: Mapped[Optional[str]] = mapped_column(Text)
    cluster_type: Mapped[Optional[str]] = mapped_column(Text)
    kubernetes_version: Mapped[Optional[str]] = mapped_column(Text)
    cloud_provider: Mapped[Optional[str]] = mapped_column(Text)
    cloud_region: Mapped[Optional[str]] = mapped_column(Text)
    cloud_zone: Mapped[Optional[str]] = mapped_column(Text)
    node_count: Mapped[Optional[int]] = mapped_column(Integer)
    node_os: Mapped[Optional[str]] = mapped_column(Text)
    node_kernel: Mapped[Optional[str]] = mapped_column(Text)
    node_architecture: Mapped[Optional[str]] = mapped_column(Text)
    node_resource_capacity: Mapped[Optional[dict]] = mapped_column(JSONB)

    run: Mapped['TestRuns'] = relationship('TestRuns', back_populates='environments')


class ResourceSnapshots(Base):
    __tablename__ = 'resource_snapshots'
    __table_args__ = (
        ForeignKeyConstraint(['run_id'], ['metadata.test_runs.run_id'], ondelete='CASCADE', name='resource_snapshots_run_id_fkey'),
        PrimaryKeyConstraint('snapshot_id', name='resource_snapshots_pkey'),
        Index('idx_resource_snapshots_run_time', 'run_id', 'snapshot_time'),
        Index('idx_resource_snapshots_test_phase', 'test_phase', 'snapshot_time'),
        Index('idx_resource_snapshots_type', 'resource_type'),
        {'schema': 'metadata'}
    )

    snapshot_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    resource_type: Mapped[ResourceType] = mapped_column(Enum(ResourceType, values_callable=lambda cls: [member.value for member in cls], name='resource_type', schema='metadata'), nullable=False)
    snapshot_time: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    node_name: Mapped[Optional[str]] = mapped_column(Text)
    namespace: Mapped[Optional[str]] = mapped_column(Text)
    pod_name: Mapped[Optional[str]] = mapped_column(Text)
    container_name: Mapped[Optional[str]] = mapped_column(Text)
    value_min: Mapped[Optional[float]] = mapped_column(Double(53))
    value_max: Mapped[Optional[float]] = mapped_column(Double(53))
    value_avg: Mapped[Optional[float]] = mapped_column(Double(53))
    value_current: Mapped[Optional[float]] = mapped_column(Double(53))
    unit: Mapped[Optional[str]] = mapped_column(Text)
    test_phase: Mapped[Optional[TestPhase]] = mapped_column(Enum(TestPhase, values_callable=lambda cls: [member.value for member in cls], name='test_phase', schema='metadata'))
    time_elapsed_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB)

    run: Mapped['TestRuns'] = relationship('TestRuns', back_populates='resource_snapshots')
