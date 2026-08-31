"""Builder for EnvironmentSpecification."""

from __future__ import annotations

from typing import TypeVar

from perfeng.generated.environment import (
    Application,
    EnvironmentSpecification,
    Kubernetes,
    NodePool,
    Runtime,
)
from perfeng.metadata.config import CollectorConfig
from perfeng.metadata.detectors import ClusterInfo, NodeInfo
from perfeng.metadata.fingerprint import generate_fingerprint

T = TypeVar("T")


def _first_not_none(*values: T | None, default: T | None = None) -> T | None:
    """Return the first non‑None value, or a default."""
    for value in values:
        if value is not None:
            return value
    return default


class EnvironmentBuilder:
    """Construct an EnvironmentSpecification from detected data and config."""

    def build(
        self,
        cluster_info: ClusterInfo,
        node_info: NodeInfo,
        k8s_version: str | None,
        node_pools: list[NodePool] | None,
        container_runtime: str | None,
        cni: str | None,
        storage_class: str | None,
        config: CollectorConfig,
    ) -> EnvironmentSpecification:
        """Combine detected information and configuration into a validated model."""
        # Resolve cluster name with a guaranteed string fallback
        cluster_name = (config.cluster.name if config.cluster else cluster_info.name) or "local"

        node_count = _first_not_none(
            config.kubernetes.node_count if config.kubernetes else None,
            cluster_info.node_count,
            1,
        )

        # Kubernetes object
        kubernetes = Kubernetes(
            version=_first_not_none(
                k8s_version,
                config.kubernetes.version if config.kubernetes else None,
            ),
            nodeCount=node_count,
            nodePools=node_pools,
        )

        # Runtime object
        runtime = Runtime(
            containerRuntime=_first_not_none(
                container_runtime,
                config.runtime.container_runtime if config.runtime else None,
            ),
            cni=_first_not_none(
                cni,
                config.runtime.cni if config.runtime else None,
            ),
            storageClass=_first_not_none(
                storage_class,
                config.runtime.storage_class if config.runtime else None,
            ),
            kernel=_first_not_none(
                node_info.kernel,
                config.runtime.kernel if config.runtime else None,
            ),
        )

        # Application object (if configured)
        application = None
        if config.application:
            application = Application(
                configurationHash=config.application.configuration_hash,
                featureFlags=config.application.feature_flags,
            )

        # Generate fingerprint
        fingerprint = generate_fingerprint(
            cluster_name=cluster_name,
            k8s_version=kubernetes.version,
            node_os=node_info.os,
            container_runtime=runtime.containerRuntime,
            excludes=list(config.fingerprint_excludes),
        )

        return EnvironmentSpecification(
            cluster=cluster_name,
            fingerprint=fingerprint,
            kubernetes=kubernetes,
            runtime=runtime,
            application=application,
            compatibility=None,
        )
