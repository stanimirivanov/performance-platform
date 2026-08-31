"""Environment collection orchestrator."""

from __future__ import annotations

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.metadata.builders.environment import (
    ApplicationBuildConfig,
    EnvironmentBuildConfig,
    EnvironmentBuilder,
    KubernetesBuildConfig,
    RuntimeBuildConfig,
)
from perfeng.metadata.config import CollectorConfig
from perfeng.metadata.detectors import KubernetesClusterDetector, LocalNodeDetector
from perfeng.metadata.merging import merge_collector_config


class EnvironmentCollector:
    """Thin orchestrator that adapts CollectorConfig, builds EnvironmentSpecification, and caches."""

    def __init__(
        self,
        config: CollectorConfig,
        local_detector: LocalNodeDetector | None = None,
        k8s_detector: KubernetesClusterDetector | None = None,
        builder: EnvironmentBuilder | None = None,
    ) -> None:
        self._config = config
        self._local_detector = local_detector or LocalNodeDetector()
        self._k8s_detector = k8s_detector or KubernetesClusterDetector(
            timeout=config.timeout_seconds
        )
        self._builder = builder
        self._cache: EnvironmentSpecification | None = None

    def collect(self, overrides: CollectorConfig | None = None) -> EnvironmentSpecification:
        """Collect environment information.

        If `overrides` is None and a cached result exists, return it.
        """
        if overrides is None and self._cache is not None:
            return self._cache

        effective_config = merge_collector_config(self._config, overrides)
        env_build_config = self._to_env_build_config(effective_config)

        if self._builder is None:
            self._builder = EnvironmentBuilder(
                config=env_build_config,
                cluster_detector=self._k8s_detector,
                node_detector=self._local_detector,
            )

        env_spec = self._builder.build()

        if overrides is None:
            self._cache = env_spec
        return env_spec

    @staticmethod
    def _to_env_build_config(config: CollectorConfig) -> EnvironmentBuildConfig:
        """Adapt broad CollectorConfig to narrow EnvironmentBuildConfig."""
        k8s = config.kubernetes
        runtime = config.runtime
        application = config.application

        return EnvironmentBuildConfig(
            auto_detect=config.auto_detect,
            cluster_name=config.cluster.name if config.cluster else None,
            kubernetes=(
                KubernetesBuildConfig(
                    version=k8s.version if k8s else None,
                    node_count=k8s.node_count if k8s else None,
                )
                if k8s
                else None
            ),
            runtime=(
                RuntimeBuildConfig(
                    container_runtime=runtime.container_runtime if runtime else None,
                    cni=runtime.cni if runtime else None,
                    storage_class=runtime.storage_class if runtime else None,
                    kernel=runtime.kernel if runtime else None,
                )
                if runtime
                else None
            ),
            application=(
                ApplicationBuildConfig(
                    configuration_hash=application.configuration_hash if application else None,
                    feature_flags=application.feature_flags if application else {},
                )
                if application
                else None
            ),
            fingerprint_excludes=config.fingerprint_excludes,
        )
