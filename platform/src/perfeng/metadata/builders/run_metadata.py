"""PerformanceRunMetadata builder and environment converter."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from perfeng.generated.environment import EnvironmentSpecification, Kubernetes, NodePool
from perfeng.generated.run_metadata import (
    Candidate,
    Data,
    PerformanceRunMetadata,
    Phases,
    Run,
    Test,
)
from perfeng.generated.run_metadata import Environment as RunEnvironment
from perfeng.generated.run_metadata import Runtime as RunRuntime
from perfeng.metadata.builders.config import EnvironmentOverrideConfig, RunMetadataBuildConfig
from perfeng.metadata.builders.mappers import (
    PROFILE_MAPPER,
    STATUS_MAPPER,
    TOOL_MAPPER,
    TRIGGER_MAPPER,
    TYPE_MAPPER,
)


class RunMetadataBuilder:
    """Builds PerformanceRunMetadata from typed config and a built EnvironmentSpecification."""

    def __init__(self, config: RunMetadataBuildConfig) -> None:
        self._config = config

    def build(self, env_spec: EnvironmentSpecification) -> PerformanceRunMetadata:
        return PerformanceRunMetadata(
            run=self._build_run(),
            test=self._build_test(),
            candidate=self._build_candidate(),
            environment=EnvironmentConverter.convert(env_spec, self._config.environment),
            runtime=self._build_runtime(),
            data=self._build_data(),
            phases=self._build_phases(),
        )

    def _build_run(self) -> Run:
        cfg = self._config.run
        now = datetime.now(UTC)
        run_id = f"perf-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

        return Run(
            id=run_id,
            suite=self._config.test_name,
            profile=PROFILE_MAPPER.map(cfg.profile),
            timestamp=now,
            trigger=TRIGGER_MAPPER.map(cfg.trigger),
            status=STATUS_MAPPER.map(self._config.status),
            policyVersion=cfg.policy_version,
            notes=cfg.notes,
        )

    def _build_test(self) -> Test:
        cfg = self._config.test
        return Test(
            type=TYPE_MAPPER.map(cfg.test_type),
            tool=TOOL_MAPPER.map(cfg.tool),
            toolVersion=cfg.tool_version,
            scenario=cfg.scenario or self._config.test_name,
            workloadVersion=cfg.workload_version,
            configHash=cfg.config_hash,
        )

    def _build_candidate(self) -> Candidate:
        cfg = self._config.candidate
        feature_flags = dict(cfg.feature_flags)
        if cfg.tags is not None:
            feature_flags["tags"] = cfg.tags
        if cfg.thresholds is not None:
            feature_flags["thresholds"] = cfg.thresholds

        return Candidate(
            gitSha=cfg.git_sha,
            imageDigest=cfg.image_digest,
            version=cfg.version,
            branch=cfg.branch,
            configurationHash=cfg.configuration_hash,
            featureFlags=feature_flags if feature_flags else None,
            databaseMigrationVersion=cfg.database_migration_version,
        )

    def _build_runtime(self) -> RunRuntime | None:
        cfg = self._config.runtime
        if cfg is None:
            return None
        return RunRuntime(
            replicas=cfg.replicas,
            cpuRequests=cfg.cpu_requests,
            cpuLimits=cfg.cpu_limits,
            memoryRequests=cfg.memory_requests,
            memoryLimits=cfg.memory_limits,
            hpa=cfg.hpa,
        )

    def _build_data(self) -> Data | None:
        cfg = self._config.data
        if cfg is None:
            return None
        return Data(
            datasetId=cfg.dataset_id,
            datasetVersion=cfg.dataset_version,
            databaseSize=cfg.database_size,
            seedVersion=cfg.seed_version,
        )

    def _build_phases(self) -> Phases | None:
        cfg = self._config.phases
        if cfg is None:
            return None
        return Phases(
            provisionStart=cfg.provision_start,
            warmupStart=cfg.warmup_start,
            measurementStart=cfg.measurement_start,
            measurementEnd=cfg.measurement_end,
            cooldownEnd=cfg.cooldown_end,
        )


class EnvironmentConverter:
    """Converts EnvironmentSpecification into the run-metadata Environment model."""

    @classmethod
    def convert(
        cls,
        env_spec: EnvironmentSpecification,
        overrides: EnvironmentOverrideConfig,
    ) -> RunEnvironment:
        kubernetes = env_spec.kubernetes
        runtime = env_spec.runtime

        primary_pool = cls._primary_pool(kubernetes)
        node_pool = overrides.node_pool or (primary_pool.name if primary_pool else None)
        cpu_arch = overrides.cpu_architecture or cls._cpu_arch(primary_pool)

        k8s_version = kubernetes.version if kubernetes and kubernetes.version else "0.0.0"

        return RunEnvironment(
            cluster=env_spec.cluster,
            kubernetesVersion=k8s_version,
            nodePool=node_pool,
            nodeModel=overrides.node_model,
            cpuArchitecture=cpu_arch,
            kernel=runtime.kernel if runtime else None,
            containerRuntime=runtime.containerRuntime if runtime else None,
            cni=runtime.cni if runtime else None,
            storageClass=runtime.storageClass if runtime else None,
            fingerprint=env_spec.fingerprint,
            nodeCount=kubernetes.nodeCount if kubernetes else None,
            region=overrides.region,
        )

    @staticmethod
    def _primary_pool(k8s: Kubernetes | None) -> NodePool | None:
        return k8s.nodePools[0] if k8s and k8s.nodePools else None

    @staticmethod
    def _cpu_arch(pool: NodePool | None) -> str | None:
        return pool.cpuArchitecture.value if pool and pool.cpuArchitecture else None
