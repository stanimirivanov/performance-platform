"""Metadata collector facade."""

from __future__ import annotations

from typing import Any

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.metadata.builders import EnvironmentBuilder, RunMetadataBuilder
from perfeng.metadata.builders.config import RunMetadataBuildConfig
from perfeng.metadata.config import CollectorConfig, load_collector_config
from perfeng.metadata.detectors import KubernetesClusterDetector, LocalNodeDetector
from perfeng.metadata.environment_collector import EnvironmentCollector
from perfeng.metadata.run_metadata_collector import RunMetadataCollector


class MetadataCollector:
    """Facade that delegates to environment and run metadata collectors."""

    def __init__(
        self,
        config: CollectorConfig | None = None,
        local_detector: LocalNodeDetector | None = None,
        k8s_detector: KubernetesClusterDetector | None = None,
        env_builder: EnvironmentBuilder | None = None,
        run_builder: RunMetadataBuilder | None = None,
    ) -> None:
        self._config = config or load_collector_config()
        self._env_collector = EnvironmentCollector(
            config=self._config,
            local_detector=local_detector,
            k8s_detector=k8s_detector,
            builder=env_builder,
        )
        self._run_collector = RunMetadataCollector(builder=run_builder)

    @property
    def config(self) -> CollectorConfig:
        return self._config

    def collect_environment(
        self, config_override: CollectorConfig | None = None
    ) -> EnvironmentSpecification:
        """Collect environment information using the given config.

        Args:
            config_override: Optional CollectorConfig to use instead of the
                one stored in the collector. If provided, the result is not
                cached.

        Returns:
            EnvironmentSpecification built from config and live detectors.
        """
        return self._env_collector.collect(overrides=config_override)

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
        return self._run_collector.collect(env_spec, run_metadata_config)


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
