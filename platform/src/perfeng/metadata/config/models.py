"""Typed configuration models for metadata collection."""

from __future__ import annotations

from dataclasses import dataclass, field

from perfeng.metadata.types import FeatureFlags, FingerprintExcludes


@dataclass(frozen=True, slots=True)
class ClusterConfig:
    """Cluster identification settings."""

    name: str | None = None
    type: str | None = None


@dataclass(frozen=True, slots=True)
class KubernetesConfig:
    """Kubernetes-specific configuration."""

    version: str | None = None
    node_count: int | None = None
    node_pools: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Container runtime and related settings."""

    container_runtime: str | None = None
    cni: str | None = None
    storage_class: str | None = None
    kernel: str | None = None


@dataclass(frozen=True, slots=True)
class ApplicationConfig:
    """Application-level configuration."""

    configuration_hash: str | None = None
    feature_flags: FeatureFlags = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CollectorConfig:
    """Top-level configuration for the metadata collector.

    Attributes:
        auto_detect: Whether to run automatic environment detection.
        timeout_seconds: Timeout for external commands (kubectl, etc.).
        fingerprint_excludes: Tuple of strings to exclude from fingerprint generation.
        cluster: Optional cluster identification config.
        kubernetes: Optional Kubernetes config.
        runtime: Optional runtime config.
        application: Optional application config.
    """

    auto_detect: bool = True
    timeout_seconds: int = 30
    fingerprint_excludes: FingerprintExcludes = ()
    cluster: ClusterConfig | None = None
    kubernetes: KubernetesConfig | None = None
    runtime: RuntimeConfig | None = None
    application: ApplicationConfig | None = None
