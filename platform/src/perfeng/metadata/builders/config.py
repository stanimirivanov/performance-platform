"""Typed configuration for RunMetadataBuilder."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class RunConfig:
    profile: str = "regression"
    trigger: str = "manual"
    policy_version: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class ExecutorConfig:
    tool: str = "k6"
    tool_version: str = "unknown"
    test_type: str = "api"
    scenario: str | None = None
    workload_version: str | None = None
    config_hash: str | None = None


@dataclass(frozen=True, slots=True)
class CandidateConfig:
    git_sha: str = "0" * 40
    image_digest: str | None = None
    version: str | None = None
    branch: str | None = None
    configuration_hash: str | None = None
    feature_flags: dict[str, Any] = field(default_factory=dict)
    tags: list[str] | None = None
    thresholds: dict[str, Any] | None = None
    database_migration_version: str | None = None


@dataclass(frozen=True, slots=True)
class RunRuntimeConfig:
    replicas: int | None = None
    cpu_requests: str | None = None
    cpu_limits: str | None = None
    memory_requests: str | None = None
    memory_limits: str | None = None
    hpa: Any | None = None


@dataclass(frozen=True, slots=True)
class DataConfig:
    dataset_id: str | None = None
    dataset_version: str | None = None
    database_size: str | None = None
    seed_version: str | None = None


@dataclass(frozen=True, slots=True)
class PhasesConfig:
    provision_start: datetime | None = None
    warmup_start: datetime | None = None
    measurement_start: datetime | None = None
    measurement_end: datetime | None = None
    cooldown_end: datetime | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentOverrideConfig:
    node_pool: str | None = None
    node_model: str | None = None
    cpu_architecture: str | None = None
    region: str | None = None


@dataclass(frozen=True, slots=True)
class RunMetadataBuildConfig:
    """Complete typed input for RunMetadataBuilder."""

    test_name: str
    status: str = "created"
    run: RunConfig = field(default_factory=RunConfig)
    test: ExecutorConfig = field(default_factory=ExecutorConfig)
    candidate: CandidateConfig = field(default_factory=CandidateConfig)
    runtime: RunRuntimeConfig | None = None
    data: DataConfig | None = None
    phases: PhasesConfig | None = None
    environment: EnvironmentOverrideConfig = field(default_factory=EnvironmentOverrideConfig)
