"""
Unit tests for the generated environment schema models.
Tests validation, serialization, and model behavior using builders.
"""

import json

import pytest
from pydantic import ValidationError

from perfeng.generated.environment import CpuArchitecture, EnvironmentSpecification, Status
from perfeng.metadata.collector import MetadataCollector
from tests.helpers.builders.builders_legacy import (
    ApplicationBuilder,
    CompatibilityBuilder,
    EnvironmentBuilder,
    KubernetesBuilder,
    NodePoolBuilder,
    RuntimeBuilder,
    default_environment_builder,
    default_kubernetes_builder,
    default_node_pool_builder,
    default_runtime_builder,
)

# -----------------------------------------------------------------------------
# Fixtures (local to this test module)
# -----------------------------------------------------------------------------


@pytest.fixture
def collector() -> MetadataCollector:
    """Return a collector with auto_detect disabled for testing."""
    from perfeng.metadata.config import CollectorConfig

    config = CollectorConfig(auto_detect=False)
    return MetadataCollector(config=config)


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


class TestEnvironmentSpecification:
    """Tests for the EnvironmentSpecification model."""

    def test_minimal_valid_environment(self):
        """Test that a minimal valid environment passes validation."""
        env = (
            EnvironmentBuilder().with_cluster("minimal-cluster").with_fingerprint("a" * 64).build()
        )
        assert env.cluster == "minimal-cluster"
        assert env.fingerprint == "a" * 64
        assert env.kubernetes is None
        assert env.runtime is None
        assert env.application is None
        assert env.compatibility is None

    def test_full_environment(self):
        """Test a full environment with all fields populated."""
        kubernetes = KubernetesBuilder().with_version("v1.28.0").with_node_count(3).build()
        runtime = (
            RuntimeBuilder()
            .with_container_runtime("containerd")
            .with_cni("calico")
            .with_storage_class("standard")
            .with_kernel("5.15.0")
            .build()
        )
        application = (
            ApplicationBuilder()
            .with_configuration_hash("config123")
            .with_feature_flags({"debug": True, "trace": False})
            .build()
        )
        env = (
            EnvironmentBuilder()
            .with_cluster("test-cluster")
            .with_fingerprint("a" * 64)
            .with_kubernetes(kubernetes)
            .with_runtime(runtime)
            .with_application(application)
            .build()
        )

        assert env.cluster == "test-cluster"
        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.28.0"
        assert env.kubernetes.nodeCount == 3
        assert env.runtime is not None
        assert env.runtime.containerRuntime == "containerd"
        assert env.application is not None
        assert env.application.configurationHash == "config123"

    def test_invalid_fingerprint(self):
        """Test that an invalid fingerprint raises ValidationError."""
        with pytest.raises(ValidationError):
            (EnvironmentBuilder().with_cluster("test").with_fingerprint("not-a-hex-string").build())

    def test_fingerprint_pattern_hex_only(self):
        """Test that fingerprint must be 64 hex characters."""
        # Valid hex
        env = (
            EnvironmentBuilder()
            .with_cluster("test")
            .with_fingerprint("abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789")
            .build()
        )
        assert env.fingerprint is not None

        # Too short
        with pytest.raises(ValidationError):
            (EnvironmentBuilder().with_cluster("test").with_fingerprint("a" * 63).build())

        # Non-hex character
        with pytest.raises(ValidationError):
            (EnvironmentBuilder().with_cluster("test").with_fingerprint("g" * 64).build())

    def test_cluster_min_length(self):
        """Test that cluster name must have at least 1 character."""
        with pytest.raises(ValidationError):
            (EnvironmentBuilder().with_cluster("").with_fingerprint("a" * 64).build())

    def test_kubernetes_version_pattern(self):
        """Test that Kubernetes version follows the expected pattern."""
        valid_versions = ["1.28.0", "v1.27.3", "1.26.5"]
        for version in valid_versions:
            k8s = KubernetesBuilder().with_version(version).with_node_count(1).build()
            env = default_environment_builder().with_kubernetes(k8s).build()
            assert env.kubernetes is not None
            assert env.kubernetes.version == version

        invalid_versions = ["1.28", "v1.28", "1.28.0.1", "v1.28.0-beta", "latest"]
        for version in invalid_versions:
            with pytest.raises(ValidationError):
                KubernetesBuilder().with_version(version).with_node_count(1).build()

    def test_node_count_minimum(self):
        """Test that node_count must be at least 1."""
        # Valid
        k8s = KubernetesBuilder().with_version("1.28.0").with_node_count(1).build()
        env = default_environment_builder().with_kubernetes(k8s).build()
        assert env.kubernetes is not None
        assert env.kubernetes.nodeCount == 1

        # Invalid: 0
        with pytest.raises(ValidationError):
            (KubernetesBuilder().with_version("1.28.0").with_node_count(0).build())

        # Invalid: negative
        with pytest.raises(ValidationError):
            (KubernetesBuilder().with_version("1.28.0").with_node_count(-1).build())

    def test_node_pool_model(self):
        """Test NodePool model validation."""
        # Valid node pool
        node_pool = default_node_pool_builder().with_name("pool-1").with_cpu_count(4).build()
        assert node_pool.name == "pool-1"
        assert node_pool.cpuCount == 4
        assert node_pool.cpuArchitecture == CpuArchitecture.amd64

        # CPU architecture enum
        assert CpuArchitecture.amd64.value == "amd64"
        assert CpuArchitecture.arm64.value == "arm64"

        # Invalid architecture
        with pytest.raises(ValidationError):
            (
                NodePoolBuilder()
                .with_name("pool-1")
                .with_node_model("test")
                .with_cpu_architecture("invalid_arch")  # type: ignore
                .with_cpu_count(2)
                .with_memory_gi_b(8.0)
                .build()
            )

        # CPU count minimum
        with pytest.raises(ValidationError):
            (
                NodePoolBuilder()
                .with_name("pool-1")
                .with_node_model("test")
                .with_cpu_architecture(CpuArchitecture.amd64)
                .with_cpu_count(0)
                .with_memory_gi_b(8.0)
                .build()
            )

        # Memory GiB minimum (0 is allowed)
        node_pool_zero = (
            NodePoolBuilder()
            .with_name("pool-1")
            .with_node_model("test")
            .with_cpu_architecture(CpuArchitecture.amd64)
            .with_cpu_count(2)
            .with_memory_gi_b(0.0)
            .build()
        )
        assert node_pool_zero.memoryGiB == 0.0

        # Negative memory is invalid
        with pytest.raises(ValidationError):
            (
                NodePoolBuilder()
                .with_name("pool-1")
                .with_node_model("test")
                .with_cpu_architecture(CpuArchitecture.amd64)
                .with_cpu_count(2)
                .with_memory_gi_b(-1.0)
                .build()
            )

    def test_runtime_model(self):
        """Test Runtime model."""
        runtime = default_runtime_builder().with_container_runtime("containerd").build()
        assert runtime.containerRuntime == "containerd"

        # All fields are optional, builder will set them to None by default
        runtime_empty = RuntimeBuilder().build()
        assert runtime_empty.containerRuntime is None
        assert runtime_empty.cni is None
        assert runtime_empty.storageClass is None
        assert runtime_empty.kernel is None

    def test_application_model(self):
        """Test Application model."""
        app = (
            ApplicationBuilder()
            .with_configuration_hash("abc123")
            .with_feature_flags({"enabled": True, "mode": "fast"})
            .build()
        )
        assert app.configurationHash == "abc123"
        assert app.featureFlags is not None
        assert app.featureFlags["mode"] == "fast"

        # Feature flags with null
        app_nulls = (
            ApplicationBuilder()
            .with_configuration_hash("hash")
            .with_feature_flags({"nullable": None, "number": 42.5})
            .build()
        )
        assert app_nulls.featureFlags is not None
        assert app_nulls.featureFlags["nullable"] is None

        # Invalid feature flag (list)
        with pytest.raises(ValidationError):
            (
                ApplicationBuilder()
                .with_configuration_hash("hash")
                .with_feature_flags({"bad": ["list"]})  # type: ignore
                .build()
            )

    def test_compatibility_model(self):
        """Test Compatibility model."""
        compat = (
            CompatibilityBuilder()
            .with_status(Status.COMPATIBLE)
            .with_reasons(["All checks passed"])
            .build()
        )
        assert compat.status == Status.COMPATIBLE
        assert compat.reasons == ["All checks passed"]

        # Invalid status
        with pytest.raises(ValidationError):
            (
                CompatibilityBuilder()
                .with_status("unknown")  # type: ignore
                .with_reasons([])
                .build()
            )

    def test_environment_serialization(self):
        """Test serialization to JSON."""
        env = (
            default_environment_builder()
            .with_kubernetes(default_kubernetes_builder().build())
            .with_runtime(default_runtime_builder().build())
            .build()
        )
        json_str = env.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["cluster"] == "test-cluster"
        assert parsed["kubernetes"]["version"] == "v1.28.0"

    def test_environment_deserialization(self):
        """Test deserialization from JSON."""
        env = default_environment_builder().build()
        json_str = env.model_dump_json()
        reconstructed = EnvironmentSpecification.model_validate_json(json_str)
        assert reconstructed.cluster == env.cluster
        assert reconstructed.fingerprint == env.fingerprint

    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed."""
        data = {
            "cluster": "test",
            "fingerprint": "a" * 64,
            "extra_field": "should not be allowed",
            "kubernetes": None,
            "runtime": None,
            "application": None,
            "compatibility": None,
        }
        with pytest.raises(ValidationError):
            EnvironmentSpecification(**data)

    def test_optional_fields_handling(self):
        """Test proper handling of optional fields."""
        # Environment with only cluster and fingerprint
        env = EnvironmentBuilder().with_cluster("test").with_fingerprint("a" * 64).build()
        assert env.kubernetes is None
        assert env.runtime is None
        assert env.application is None
        assert env.compatibility is None

        # Environment with kubernetes only
        k8s = KubernetesBuilder().with_version("1.28.0").with_node_count(2).build()
        env = default_environment_builder().with_kubernetes(k8s).build()
        assert env.kubernetes is not None
        assert env.kubernetes.version == "1.28.0"

    def test_fingerprint_generation_not_automatic(self):
        """Test that fingerprint is required and not auto-generated."""
        with pytest.raises(ValidationError):
            # Missing fingerprint
            EnvironmentSpecification(
                cluster="test",
            )  # type: ignore

    def test_model_dump_with_exclude(self):
        """Test model_dump with exclude options."""
        env = (
            default_environment_builder()
            .with_kubernetes(default_kubernetes_builder().build())
            .build()
        )
        dumped = env.model_dump(exclude={"kubernetes"})
        assert "kubernetes" not in dumped
        assert dumped["cluster"] == "test-cluster"


class TestEnvironmentModelIntegration:
    """Integration tests with the metadata collector."""

    def test_collector_returns_valid_environment(self, collector):
        """Test that the collector returns a valid EnvironmentSpecification."""
        env = collector.collect_environment()
        assert isinstance(env, EnvironmentSpecification)
        assert env.cluster is not None
        assert len(env.fingerprint) == 64
        assert env.model_dump() is not None

    def test_environment_from_collector_is_json_serializable(self, collector):
        """Test that the collected environment can be serialized to JSON."""
        env = collector.collect_environment()
        json_str = env.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["cluster"] == env.cluster
        assert parsed["fingerprint"] == env.fingerprint

    def test_environment_roundtrip_with_collector(self, collector):
        """Test roundtrip: collect -> serialize -> deserialize -> compare."""
        original = collector.collect_environment()
        json_str = original.model_dump_json()
        reconstructed = EnvironmentSpecification.model_validate_json(json_str)

        assert reconstructed.cluster == original.cluster
        assert reconstructed.fingerprint == original.fingerprint

        if original.kubernetes is not None:
            assert reconstructed.kubernetes is not None
            assert reconstructed.kubernetes.version == original.kubernetes.version
            assert reconstructed.kubernetes.nodeCount == original.kubernetes.nodeCount
        else:
            assert reconstructed.kubernetes is None

        if original.runtime is not None:
            assert reconstructed.runtime is not None
            assert reconstructed.runtime.containerRuntime == original.runtime.containerRuntime
        else:
            assert reconstructed.runtime is None

        if original.application is not None:
            assert reconstructed.application is not None
            assert (
                reconstructed.application.configurationHash
                == original.application.configurationHash
            )
        else:
            assert reconstructed.application is None
