"""Metadata collector orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.metadata.builders import EnvironmentBuilder, RunMetadataBuilder, TestMetadata
from perfeng.metadata.config import CollectorConfig, load_collector_config
from perfeng.metadata.detectors import (
    ClusterInfo,
    KubernetesClusterDetector,
    LocalNodeDetector,
    NodeInfo,
)


@dataclass(frozen=True, slots=True)
class MetadataOverrides:
    """Explicit overrides for metadata collection.

    Attributes are optional; any non‑None value will override the
    automatically detected or configured value.
    """

    cluster_name: str | None = None
    cluster_type: str | None = None
    node_count: int | None = None
    kubernetes_version: str | None = None
    container_runtime: str | None = None
    cni: str | None = None
    storage_class: str | None = None
    kernel: str | None = None
    node_pool: str | None = None
    node_model: str | None = None
    cpu_architecture: str | None = None
    region: str | None = None
    # Additional test metadata overrides
    test_metadata: TestMetadata | None = None


class MetadataCollector:
    """Collects environment and test metadata using typed detectors and builders.

    The collector orchestrates:
        1. Loading configuration (typed `CollectorConfig`).
        2. Running local and Kubernetes detectors.
        3. Building `EnvironmentSpecification` via `EnvironmentBuilder`.
        4. Building `PerformanceRunMetadata` via `RunMetadataBuilder`.

    Detectors and builders can be injected for testability.
    """

    def __init__(
        self,
        config: CollectorConfig | None = None,
        local_detector: LocalNodeDetector | None = None,
        k8s_detector: KubernetesClusterDetector | None = None,
        env_builder: EnvironmentBuilder | None = None,
        run_builder: RunMetadataBuilder | None = None,
    ) -> None:
        self._config = config or load_collector_config()
        self._local_detector = local_detector or LocalNodeDetector()
        self._k8s_detector = k8s_detector or KubernetesClusterDetector(
            timeout=self._config.timeout_seconds
        )
        self._env_builder = env_builder or EnvironmentBuilder()
        self._run_builder = run_builder or RunMetadataBuilder()

        self._environment_cache: EnvironmentSpecification | None = None

    @property
    def config(self) -> CollectorConfig:
        return self._config

    def collect_environment(
        self,
        overrides: MetadataOverrides | None = None,
    ) -> EnvironmentSpecification:
        """Collect and build environment information.

        Results are cached; use `overrides` to force rebuilding with different values.
        """
        if overrides is None and self._environment_cache is not None:
            return self._environment_cache

        # 1. Detect local node info
        node_info = self._local_detector.detect()

        # 2. Detect Kubernetes cluster info (if auto_detect enabled)
        cluster_info: ClusterInfo
        k8s_version: str | None = None
        node_pools: list | None = None
        container_runtime: str | None = None
        cni: str | None = None
        storage_class: str | None = None

        if self._config.auto_detect:
            cluster_info = self._k8s_detector.detect()
            if cluster_info.type.value == "k8s":
                k8s_version = self._k8s_detector.detect_version()
                node_pools = self._k8s_detector.detect_node_pools()
                container_runtime = self._k8s_detector.detect_container_runtime()
                cni = self._k8s_detector.detect_cni()
                storage_class = self._k8s_detector.detect_storage_class()
            else:
                # Fallback to local/docker
                k8s_version = None
                node_pools = None
                container_runtime = None
                cni = None
                storage_class = None
        else:
            # No auto-detection: use config or defaults
            cluster_info = ClusterInfo(
                name=self._config.cluster.name if self._config.cluster else "local",
                type=(self._config.cluster.type if self._config.cluster else "local").lower(),
                node_count=(self._config.kubernetes.node_count if self._config.kubernetes else 1),
            )
            k8s_version = self._config.kubernetes.version if self._config.kubernetes else None
            node_pools = None
            container_runtime = (
                self._config.runtime.container_runtime if self._config.runtime else None
            )
            cni = self._config.runtime.cni if self._config.runtime else None
            storage_class = self._config.runtime.storage_class if self._config.runtime else None

        # 3. Apply overrides
        if overrides:
            cluster_info = ClusterInfo(
                name=overrides.cluster_name or cluster_info.name,
                type=ClusterType(overrides.cluster_type or cluster_info.type.value),
                node_count=overrides.node_count or cluster_info.node_count,
            )
            if overrides.kubernetes_version is not None:
                k8s_version = overrides.kubernetes_version
            if overrides.container_runtime is not None:
                container_runtime = overrides.container_runtime
            if overrides.cni is not None:
                cni = overrides.cni
            if overrides.storage_class is not None:
                storage_class = overrides.storage_class
            if overrides.kernel is not None:
                node_info = NodeInfo(
                    os=node_info.os,
                    kernel=overrides.kernel,
                    architecture=node_info.architecture,
                    resources=node_info.resources,
                )

        # 4. Build environment spec
        env_spec = self._env_builder.build(
            cluster_info=cluster_info,
            node_info=node_info,
            k8s_version=k8s_version,
            node_pools=node_pools,
            container_runtime=container_runtime,
            cni=cni,
            storage_class=storage_class,
            config=self._config,
        )

        if overrides is None:
            self._environment_cache = env_spec
        return env_spec

    def collect_test_metadata(
        self,
        test_name: str,
        status: str = "CREATED",
        test_metadata: TestMetadata | None = None,
        environment_overrides: MetadataOverrides | None = None,
    ) -> PerformanceRunMetadata:
        """Collect complete test metadata and build the Pydantic model.

        Args:
            test_name: Name of the test (suite).
            status: Initial run status (mapped to RunStatus).
            test_metadata: Structured test parameters.
            environment_overrides: Optional environment overrides.

        Returns:
            A fully populated PerformanceRunMetadata.
        """
        env_spec = self.collect_environment(overrides=environment_overrides)

        meta = test_metadata or TestMetadata()
        return self._run_builder.build(
            test_name=test_name,
            status=status,
            env_spec=env_spec,
            test_metadata=meta,
        )


# -----------------------------------------------------------------------------
# Convenience functions
# -----------------------------------------------------------------------------


def get_metadata_collector(
    env_type: str | None = None,
) -> MetadataCollector:
    """Factory function that returns a MetadataCollector with config loaded."""
    config = load_collector_config(env_type)
    return MetadataCollector(config=config)


def collect_run_metadata(
    test_name: str,
    status: str = "CREATED",
    test_metadata: TestMetadata | None = None,
    env_type: str | None = None,
) -> dict[str, Any]:
    """Convenience function to collect run metadata and return as a dict.

    Args:
        test_name: Name of the test.
        status: Initial status.
        test_metadata: Structured test parameters.
        env_type: Environment type for configuration loading.

    Returns:
        Dictionary representation of the run metadata.
    """
    collector = get_metadata_collector(env_type)
    metadata = collector.collect_test_metadata(test_name, status, test_metadata)
    return metadata.model_dump(exclude_none=True)
