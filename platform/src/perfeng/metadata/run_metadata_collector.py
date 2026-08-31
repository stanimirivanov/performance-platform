"""Run metadata collection orchestrator."""

from __future__ import annotations

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.metadata.builders import RunMetadataBuilder
from perfeng.metadata.builders.config import RunMetadataBuildConfig


class RunMetadataCollector:
    """Thin orchestrator that builds PerformanceRunMetadata from config and environment."""

    def __init__(self, builder: RunMetadataBuilder | None = None) -> None:
        self._builder = builder

    def collect(
        self,
        env_spec: EnvironmentSpecification,
        config: RunMetadataBuildConfig,
    ) -> PerformanceRunMetadata:
        if self._builder is None:
            self._builder = RunMetadataBuilder(config)
        return self._builder.build(env_spec)
