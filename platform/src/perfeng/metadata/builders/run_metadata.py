"""Builder for PerformanceRunMetadata."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import (
    Candidate,
    Data,
    Hpa,
    PerformanceRunMetadata,
    Phases,
    Profile,
    Run,
    Test,
    Trigger,
)
from perfeng.generated.run_metadata import Environment as RunEnvironment
from perfeng.generated.run_metadata import Runtime as RunRuntime
from perfeng.generated.run_metadata import Status as RunStatus
from perfeng.generated.run_metadata import Tool as TestTool
from perfeng.generated.run_metadata import Type as TestType


@dataclass(frozen=True, slots=True)
class TestMetadata:
    """Structured test parameters used to build run metadata.

    All fields are optional and correspond to the high‑level metadata model.
    """

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
    hpa: Hpa | None = None

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


class RunMetadataBuilder:
    """Build a complete PerformanceRunMetadata instance from typed inputs."""

    _STATUS_MAP = {
        "created": RunStatus.CREATED,
        "validating": RunStatus.VALIDATING,
        "provisioning": RunStatus.PROVISIONING,
        "warming_up": RunStatus.WARMING_UP,
        "running": RunStatus.RUNNING,
        "collecting": RunStatus.COLLECTING,
        "analyzing": RunStatus.ANALYZING,
        "reporting": RunStatus.REPORTING,
        "completed": RunStatus.COMPLETED,
        "invalid": RunStatus.INVALID,
        "aborted": RunStatus.ABORTED,
        "infrastructure_failure": RunStatus.INFRASTRUCTURE_FAILURE,
        "test_failure": RunStatus.TEST_FAILURE,
        "inconclusive": RunStatus.INCONCLUSIVE,
    }

    _PROFILE_MAP = {
        "smoke": Profile.smoke,
        "average": Profile.average,
        "regression": Profile.regression,
        "stress": Profile.stress,
        "capacity": Profile.capacity,
        "soak": Profile.soak,
    }

    _TRIGGER_MAP = {
        "manual": Trigger.manual,
        "ci": Trigger.ci,
        "schedule": Trigger.schedule,
        "bisect": Trigger.bisect,
        "release": Trigger.release,
    }

    _TOOL_MAP = {
        "k6": TestTool.k6,
        "playwright": TestTool.playwright,
        "kube-burner": TestTool.kube_burner,
        "benchmark-operator": TestTool.benchmark_operator,
    }

    _TYPE_MAP = {
        "api": TestType.api,
        "browser": TestType.browser,
        "kubernetes": TestType.kubernetes,
        "infrastructure": TestType.infrastructure,
    }

    def build(
        self,
        test_name: str,
        status: str,
        env_spec: EnvironmentSpecification,
        test_metadata: TestMetadata,
    ) -> PerformanceRunMetadata:
        """Create a PerformanceRunMetadata instance."""
        run = self._build_run(test_name, status, test_metadata)
        test = self._build_test(test_name, test_metadata)
        candidate = self._build_candidate(test_metadata)
        env = self._build_environment(env_spec, test_metadata)
        runtime = self._build_runtime(test_metadata)
        data = self._build_data(test_metadata)
        phases = self._build_phases(test_metadata)

        return PerformanceRunMetadata(
            run=run,
            test=test,
            candidate=candidate,
            environment=env,
            runtime=runtime,
            data=data,
            phases=phases,
        )

    def _build_run(self, test_name: str, status: str, meta: TestMetadata) -> Run:
        now = datetime.now(UTC)
        suffix = uuid.uuid4().hex[:8]
        run_id = f"perf-{now.strftime('%Y%m%d-%H%M%S')}-{suffix}"

        run_status = self._STATUS_MAP.get(status.lower(), RunStatus.CREATED)
        profile = self._PROFILE_MAP.get(meta.test_profile.lower(), Profile.regression)
        trigger = self._TRIGGER_MAP.get(meta.trigger_type.lower(), Trigger.manual)

        return Run(
            id=run_id,
            suite=test_name,
            profile=profile,
            timestamp=now,
            trigger=trigger,
            status=run_status,
            policyVersion=meta.policy_version,
            notes=meta.notes,
        )

    def _build_test(self, test_name: str, meta: TestMetadata) -> Test:
        tool = self._TOOL_MAP.get(meta.tool.lower(), TestTool.k6)
        test_type = self._TYPE_MAP.get(meta.test_type.lower(), TestType.api)

        return Test(
            type=test_type,
            tool=tool,
            toolVersion=meta.tool_version or "unknown",
            scenario=meta.scenario or test_name,
            workloadVersion=None,  # set via meta if needed later
            configHash=meta.configuration_hash,
        )

    def _build_candidate(self, meta: TestMetadata) -> Candidate:
        feature_flags = meta.feature_flags if meta.feature_flags else None
        return Candidate(
            gitSha=meta.git_sha,
            imageDigest=None,  # not in TestMetadata yet
            version=meta.version,
            branch=meta.branch,
            configurationHash=meta.configuration_hash,
            featureFlags=feature_flags,
            databaseMigrationVersion=meta.database_migration_version,
        )

    def _build_environment(
        self, env_spec: EnvironmentSpecification, meta: TestMetadata
    ) -> RunEnvironment:
        kubernetes = env_spec.kubernetes
        runtime = env_spec.runtime

        node_pool = None
        cpu_arch = None
        if kubernetes and kubernetes.nodePools and len(kubernetes.nodePools) > 0:
            first_pool = kubernetes.nodePools[0]
            node_pool = first_pool.name
            if first_pool.cpuArchitecture:
                cpu_arch = first_pool.cpuArchitecture.value

        k8s_version = kubernetes.version if kubernetes and kubernetes.version else "0.0.0"

        return RunEnvironment(
            cluster=env_spec.cluster,
            kubernetesVersion=k8s_version,
            nodePool=meta.node_pool or node_pool,
            nodeModel=meta.node_model,
            cpuArchitecture=meta.cpu_architecture or cpu_arch,
            kernel=runtime.kernel if runtime else None,
            containerRuntime=runtime.containerRuntime if runtime else None,
            cni=runtime.cni if runtime else None,
            storageClass=runtime.storageClass if runtime else None,
            fingerprint=env_spec.fingerprint,
            nodeCount=kubernetes.nodeCount if kubernetes else None,
            region=meta.region,
        )

    def _build_runtime(self, meta: TestMetadata) -> RunRuntime | None:
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
        ):
            return RunRuntime(
                replicas=meta.replicas,
                cpuRequests=meta.cpu_requests,
                cpuLimits=meta.cpu_limits,
                memoryRequests=meta.memory_requests,
                memoryLimits=meta.memory_limits,
                hpa=meta.hpa,
            )
        return None

    def _build_data(self, meta: TestMetadata) -> Data | None:
        if any(
            v is not None
            for v in [
                meta.dataset_id,
                meta.dataset_version,
                meta.database_size,
                meta.seed_version,
            ]
        ):
            return Data(
                datasetId=meta.dataset_id,
                datasetVersion=meta.dataset_version,
                databaseSize=meta.database_size,
                seedVersion=meta.seed_version,
            )
        return None

    def _build_phases(self, meta: TestMetadata) -> Phases | None:
        if any(
            v is not None
            for v in [
                meta.provision_start,
                meta.warmup_start,
                meta.measurement_start,
                meta.measurement_end,
                meta.cooldown_end,
            ]
        ):
            return Phases(
                provisionStart=meta.provision_start,
                warmupStart=meta.warmup_start,
                measurementStart=meta.measurement_start,
                measurementEnd=meta.measurement_end,
                cooldownEnd=meta.cooldown_end,
            )
        return None
