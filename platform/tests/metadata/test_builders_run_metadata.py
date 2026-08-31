"""
Tests for RunMetadataBuilder, EnvironmentConverter, EnumMapper, and mappers.
"""

from datetime import UTC, datetime

from perfeng.generated.environment import (
    CpuArchitecture,
    EnvironmentSpecification,
    Kubernetes,
    NodePool,
    Runtime,
)
from perfeng.generated.run_metadata import (
    PerformanceRunMetadata,
    Profile,
    Status,
    Tool,
    Trigger,
    Type,
)
from perfeng.metadata.builders import EnumMapper, EnvironmentConverter, RunMetadataBuilder
from perfeng.metadata.builders.config import (
    CandidateConfig,
    DataConfig,
    EnvironmentOverrideConfig,
    ExecutorConfig,
    PhasesConfig,
    RunConfig,
    RunMetadataBuildConfig,
    RunRuntimeConfig,
)


# Sample EnvironmentSpecification
def make_env_spec() -> EnvironmentSpecification:
    return EnvironmentSpecification(
        cluster="test-cluster",
        fingerprint="a" * 64,
        kubernetes=Kubernetes(
            version="v1.28.0",
            nodeCount=3,
            nodePools=[
                NodePool(
                    name="pool-1",
                    nodeModel="m5.xlarge",
                    cpuArchitecture=CpuArchitecture.amd64,
                    cpuCount=4,
                    memoryGiB=16.0,
                )
            ],
        ),
        runtime=Runtime(
            containerRuntime="containerd",
            cni="calico",
            storageClass="standard",
            kernel="5.15.0",
        ),
        application=None,
        compatibility=None,
    )


class TestEnumMapper:
    def test_map_valid(self):
        mapper = EnumMapper({"a": Profile.regression}, Profile.regression)
        assert mapper.map("a") == Profile.regression
        assert mapper.map("A") == Profile.regression  # case-insensitive

    def test_map_invalid_uses_default(self):
        mapper = EnumMapper({"a": Profile.regression}, Profile.regression)
        assert mapper.map("unknown") == Profile.regression


class TestEnvironmentConverter:
    def test_convert(self):
        env_spec = make_env_spec()
        overrides = EnvironmentOverrideConfig(
            node_pool="override-pool",
            node_model="m5.large",
            cpu_architecture="arm64",
            region="us-east-1",
        )
        run_env = EnvironmentConverter.convert(env_spec, overrides)

        assert run_env.cluster == "test-cluster"
        assert run_env.kubernetesVersion == "v1.28.0"
        assert run_env.nodePool == "override-pool"
        assert run_env.nodeModel == "m5.large"
        assert run_env.cpuArchitecture == "arm64"
        assert run_env.fingerprint == "a" * 64
        assert run_env.nodeCount == 3
        assert run_env.region == "us-east-1"


class TestRunMetadataBuilder:
    def _make_config(self) -> RunMetadataBuildConfig:
        return RunMetadataBuildConfig(
            test_name="checkout-api",
            status="running",
            run=RunConfig(profile="smoke", trigger="ci", policy_version="1.0", notes="test"),
            test=ExecutorConfig(
                tool="k6", tool_version="0.45.0", test_type="api", scenario="checkout-flow"
            ),
            candidate=CandidateConfig(
                git_sha="a" * 40, version="1.0.0", branch="main", configuration_hash="hash"
            ),
            runtime=RunRuntimeConfig(
                replicas=2,
                cpu_requests="500m",
                cpu_limits="1000m",
                memory_requests="512Mi",
                memory_limits="1024Mi",
                hpa=None,
            ),
            data=DataConfig(dataset_id="dataset-1", dataset_version="1.0"),
            phases=PhasesConfig(measurement_start=datetime.now(UTC)),
            environment=EnvironmentOverrideConfig(),
        )

    def test_build_full(self):
        builder = RunMetadataBuilder(self._make_config())
        env_spec = make_env_spec()
        metadata = builder.build(env_spec)

        assert isinstance(metadata, PerformanceRunMetadata)
        assert metadata.run.suite == "checkout-api"
        assert metadata.run.status == Status.RUNNING
        assert metadata.run.profile == Profile.smoke
        assert metadata.run.trigger == Trigger.ci
        assert metadata.run.policyVersion == "1.0"
        assert metadata.test.tool == Tool.k6
        assert metadata.test.type == Type.api
        assert metadata.candidate.gitSha == "a" * 40
        assert metadata.runtime is not None
        assert metadata.runtime.replicas == 2
        assert metadata.data is not None
        assert metadata.data.datasetId == "dataset-1"
        assert metadata.phases is not None
        assert metadata.phases.measurementStart is not None

    def test_build_no_optional(self):
        config = RunMetadataBuildConfig(
            test_name="minimal",
            status="created",
            run=RunConfig(),
            test=ExecutorConfig(),
            candidate=CandidateConfig(),
            runtime=None,
            data=None,
            phases=None,
            environment=EnvironmentOverrideConfig(),
        )
        builder = RunMetadataBuilder(config)
        env_spec = make_env_spec()
        metadata = builder.build(env_spec)
        assert metadata.runtime is None
        assert metadata.data is None
        assert metadata.phases is None
