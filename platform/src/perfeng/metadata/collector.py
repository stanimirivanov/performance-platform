"""Metadata collector orchestrator using typed detectors and builders."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.metadata.builders import EnvironmentBuilder, RunMetadataBuildConfig, RunMetadataBuilder
from perfeng.metadata.builders.config import (
    CandidateConfig,
    DataConfig,
    EnvironmentOverrideConfig,
    PhasesConfig,
    RunConfig,
    RunRuntimeConfig,
    TestConfig,
)
from perfeng.metadata.config import CollectorConfig, load_collector_config
from perfeng.metadata.detectors import KubernetesClusterDetector, LocalNodeDetector


@dataclass(frozen=True, slots=True)
class TestMetadata:
    """Convenience structure for test parameters (backward compatible)."""

    test_profile: str = "regression"
    trigger_type: str = "manual"
    tool: str = "k6"
    test_type: str = "api"
    tool_version: str | None = None
    scenario: str | None = None
    git_sha: str = "0" * 40
    version: str | None = None
    branch: str | None = None
    configuration_hash: str | None = None
    feature_flags: dict[str, Any] = field(default_factory=dict)
    database_migration_version: str | None = None

    # Runtime resources
    replicas: int | None = None
    cpu_requests: str | None = None
    cpu_limits: str | None = None
    memory_requests: str | None = None
    memory_limits: str | None = None
    hpa: Any | None = None

    # Data
    dataset_id: str | None = None
    dataset_version: str | None = None
    database_size: str | None = None
    seed_version: str | None = None

    # Phases
    provision_start: datetime | None = None
    warmup_start: datetime | None = None
    measurement_start: datetime | None = None
    measurement_end: datetime | None = None
    cooldown_end: datetime | None = None

    # Additional
    policy_version: str | None = None
    notes: str | None = None
    node_pool: str | None = None
    node_model: str | None = None
    cpu_architecture: str | None = None
    region: str | None = None


@dataclass(frozen=True, slots=True)
class MetadataOverrides:
    """Environment overrides for the collector."""

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
        # EnvironmentBuilder requires the detectors to be passed; we pass them now.
        self._env_builder = env_builder or EnvironmentBuilder(
            config=self._config,
            cluster_detector=self._k8s_detector,
            node_detector=self._local_detector,
        )
        self._environment_cache: EnvironmentSpecification | None = None

    @property
    def config(self) -> CollectorConfig:
        return self._config

    def _apply_environment_overrides(self, overrides: MetadataOverrides | None) -> CollectorConfig:
        """Return a new CollectorConfig with overrides applied."""
        if overrides is None:
            return self._config
        # We need to construct a new config. Since CollectorConfig is frozen,
        # we use dataclasses.replace or build manually.
        import dataclasses

        new_config = dataclasses.replace(
            self._config,
            cluster=self._config.cluster,
            kubernetes=self._config.kubernetes,
            runtime=self._config.runtime,
            application=self._config.application,
        )
        # Apply overrides to relevant sub-configs.
        # For simplicity, we create new sub-config objects.
        if overrides.cluster_name or overrides.cluster_type:
            cluster = new_config.cluster or type(new_config.cluster)(name="", type="")
            cluster = dataclasses.replace(
                cluster,
                name=overrides.cluster_name or cluster.name,
                type=overrides.cluster_type or cluster.type,
            )
            new_config = dataclasses.replace(new_config, cluster=cluster)

        if overrides.node_count is not None or overrides.kubernetes_version is not None:
            k8s = new_config.kubernetes or type(new_config.kubernetes)()
            k8s = dataclasses.replace(
                k8s,
                node_count=overrides.node_count
                if overrides.node_count is not None
                else k8s.node_count,
                version=overrides.kubernetes_version
                if overrides.kubernetes_version is not None
                else k8s.version,
            )
            new_config = dataclasses.replace(new_config, kubernetes=k8s)

        if (
            overrides.container_runtime is not None
            or overrides.cni is not None
            or overrides.storage_class is not None
            or overrides.kernel is not None
        ):
            runtime = new_config.runtime or type(new_config.runtime)()
            runtime = dataclasses.replace(
                runtime,
                container_runtime=overrides.container_runtime or runtime.container_runtime,
                cni=overrides.cni or runtime.cni,
                storage_class=overrides.storage_class or runtime.storage_class,
                kernel=overrides.kernel or runtime.kernel,
            )
            new_config = dataclasses.replace(new_config, runtime=runtime)

        return new_config

    def collect_environment(
        self,
        overrides: MetadataOverrides | None = None,
    ) -> EnvironmentSpecification:
        """Collect environment information, applying optional overrides."""
        if overrides is None and self._environment_cache is not None:
            return self._environment_cache

        effective_config = self._apply_environment_overrides(overrides)

        # Create a new EnvironmentBuilder with the effective config.
        builder = EnvironmentBuilder(
            config=effective_config,
            cluster_detector=self._k8s_detector,
            node_detector=self._local_detector,
        )
        env_spec = builder.build()

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
        """Collect full test metadata and return the Pydantic model."""
        env_spec = self.collect_environment(overrides=environment_overrides)

        meta = test_metadata or TestMetadata()
        run_meta_config = self._to_run_metadata_config(test_name, status, meta)

        builder = RunMetadataBuilder(run_meta_config)
        return builder.build(env_spec)

    @staticmethod
    def _to_run_metadata_config(
        test_name: str,
        status: str,
        meta: TestMetadata,
    ) -> RunMetadataBuildConfig:
        """Convert TestMetadata to RunMetadataBuildConfig."""
        return RunMetadataBuildConfig(
            test_name=test_name,
            status=status,
            run=RunConfig(
                profile=meta.test_profile,
                trigger=meta.trigger_type,
                policy_version=meta.policy_version,
                notes=meta.notes,
            ),
            test=TestConfig(
                tool=meta.tool,
                tool_version=meta.tool_version or "unknown",
                test_type=meta.test_type,
                scenario=meta.scenario,
                workload_version=None,  # not in TestMetadata
                config_hash=meta.configuration_hash,
            ),
            candidate=CandidateConfig(
                git_sha=meta.git_sha,
                image_digest=None,
                version=meta.version,
                branch=meta.branch,
                configuration_hash=meta.configuration_hash,
                feature_flags=meta.feature_flags,
                tags=None,
                thresholds=None,
                database_migration_version=meta.database_migration_version,
            ),
            runtime=RunRuntimeConfig(
                replicas=meta.replicas,
                cpu_requests=meta.cpu_requests,
                cpu_limits=meta.cpu_limits,
                memory_requests=meta.memory_requests,
                memory_limits=meta.memory_limits,
                hpa=meta.hpa,
            )
            if any(
                v is not None
                for v in [
                    meta.replicas,
                    meta.cpu_requests,
                    meta.cpu_limits,
                    meta.memory_requests,
                    meta.memory_limits,
                    meta.hpa,
                ]
            )
            else None,
            data=DataConfig(
                dataset_id=meta.dataset_id,
                dataset_version=meta.dataset_version,
                database_size=meta.database_size,
                seed_version=meta.seed_version,
            )
            if any(
                v is not None
                for v in [
                    meta.dataset_id,
                    meta.dataset_version,
                    meta.database_size,
                    meta.seed_version,
                ]
            )
            else None,
            phases=PhasesConfig(
                provision_start=meta.provision_start,
                warmup_start=meta.warmup_start,
                measurement_start=meta.measurement_start,
                measurement_end=meta.measurement_end,
                cooldown_end=meta.cooldown_end,
            )
            if any(
                v is not None
                for v in [
                    meta.provision_start,
                    meta.warmup_start,
                    meta.measurement_start,
                    meta.measurement_end,
                    meta.cooldown_end,
                ]
            )
            else None,
            environment=EnvironmentOverrideConfig(
                node_pool=meta.node_pool,
                node_model=meta.node_model,
                cpu_architecture=meta.cpu_architecture,
                region=meta.region,
            ),
        )


# -----------------------------------------------------------------------------
# Convenience functions
# -----------------------------------------------------------------------------


def get_metadata_collector(env_type: str | None = None) -> MetadataCollector:
    """Factory function that returns a MetadataCollector with config loaded."""
    config = load_collector_config(env_type)
    return MetadataCollector(config=config)


def collect_run_metadata(
    test_name: str,
    status: str = "CREATED",
    test_metadata: TestMetadata | None = None,
    env_type: str | None = None,
    environment_overrides: MetadataOverrides | None = None,
) -> dict[str, Any]:
    """Convenience function to collect run metadata and return as a dict."""
    collector = get_metadata_collector(env_type)
    metadata = collector.collect_test_metadata(
        test_name, status, test_metadata, environment_overrides
    )
    return metadata.model_dump(exclude_none=True)
