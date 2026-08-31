"""Metadata collector orchestrator using typed detectors and builders."""

from __future__ import annotations

from typing import Any

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.metadata.builders import EnvironmentBuilder, RunMetadataBuilder
from perfeng.metadata.builders.config import RunMetadataBuildConfig
from perfeng.metadata.builders.environment import (
    ApplicationBuildConfig,
    EnvironmentBuildConfig,
    KubernetesBuildConfig,
    RuntimeBuildConfig,
)
from perfeng.metadata.config import CollectorConfig, load_collector_config
from perfeng.metadata.detectors import KubernetesClusterDetector, LocalNodeDetector


class MetadataCollector:
    """Collects environment and test metadata using typed detectors and builders."""

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
        # Note: EnvironmentBuilder is created per call to allow config overrides.
        self._environment_cache: EnvironmentSpecification | None = None

    @property
    def config(self) -> CollectorConfig:
        return self._config

    def collect_environment(
        self,
        config_override: CollectorConfig | None = None,
    ) -> EnvironmentSpecification:
        """Collect environment information using the given config.

        Args:
            config_override: Optional CollectorConfig to use instead of the
                one stored in the collector. If provided, the result is not
                cached.

        Returns:
            EnvironmentSpecification built from config and live detectors.
        """
        if config_override is None and self._environment_cache is not None:
            return self._environment_cache

        effective_config = config_override or self._config
        env_build_config = self._to_env_build_config(effective_config)

        builder = EnvironmentBuilder(
            config=env_build_config,
            cluster_detector=self._k8s_detector,
            node_detector=self._local_detector,
        )
        env_spec = builder.build()

        if config_override is None:
            self._environment_cache = env_spec
        return env_spec

    def collect_test_metadata(
        self,
        run_metadata_config: RunMetadataBuildConfig,
        env_config_override: CollectorConfig | None = None,
    ) -> PerformanceRunMetadata:
        """Collect full test metadata using a RunMetadataBuildConfig.

        Args:
            run_metadata_config: Fully specified run metadata configuration.
            env_config_override: Optional environment config override.

        Returns:
            PerformanceRunMetadata built from the config and collected environment.
        """
        env_spec = self.collect_environment(config_override=env_config_override)
        builder = RunMetadataBuilder(run_metadata_config)
        return builder.build(env_spec)

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


# -----------------------------------------------------------------------------
# Convenience functions
# -----------------------------------------------------------------------------


def get_metadata_collector(env_type: str | None = None) -> MetadataCollector:
    """Factory function that returns a MetadataCollector with config loaded."""
    config = load_collector_config(env_type)
    return MetadataCollector(config=config)


def collect_run_metadata(
    run_metadata_config: RunMetadataBuildConfig,
    env_type: str | None = None,
    env_config_override: CollectorConfig | None = None,
) -> dict[str, Any]:
    """Collect run metadata using a full RunMetadataBuildConfig.

    Returns a dictionary representation of the metadata.
    """
    collector = get_metadata_collector(env_type)
    metadata = collector.collect_test_metadata(
        run_metadata_config=run_metadata_config,
        env_config_override=env_config_override,
    )
    return metadata.model_dump(mode="json", exclude_none=True)
