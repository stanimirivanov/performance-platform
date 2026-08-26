"""
Unit tests for the metadata collector using builders.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from perfeng.generated.environment import CpuArchitecture, EnvironmentSpecification
from perfeng.generated.run_metadata import Environment as RunEnvironment
from perfeng.generated.run_metadata import Profile
from perfeng.generated.run_metadata import Status as RunStatus
from perfeng.metadata.collector import (
    MetadataCollector,
    collect_run_metadata,
    get_metadata_collector,
)
from tests.builders import (
    EnvironmentBuilder,
    KubernetesBuilder,
    RuntimeBuilder,
    default_environment_builder,
    default_kubernetes_builder,
    default_node_pool_builder,
    default_runtime_builder,
)

pytestmark = pytest.mark.metadata


class TestMetadataCollector:
    """Test cases for MetadataCollector."""

    def test_init_default(self, collector):
        """Test initialization with default settings."""
        assert collector is not None
        assert collector.config["auto_detect"] is True
        assert collector.config["timeout_seconds"] == 30
        assert collector._environment_cache is None

    def test_init_with_config(self, temp_config_file):
        """Test initialization with configuration file."""
        collector = MetadataCollector(temp_config_file)
        assert collector.config["auto_detect"] is False
        assert collector.config["environment_config"]["cluster"] == "test-cluster"

    def test_set_override(self, collector):
        """Test setting manual overrides."""
        collector.set_override("test_key", "test_value")
        assert collector.override_values["test_key"] == "test_value"

        # Override environment
        collector.set_override("environment", {"cluster": "override-cluster"})
        assert collector.override_values["environment"]["cluster"] == "override-cluster"

    def test_collect_environment_from_config(self, collector_with_config):
        """Test collecting environment from configuration only."""
        env = collector_with_config.collect_environment()

        assert isinstance(env, EnvironmentSpecification)
        assert env.cluster == "test-cluster"
        assert env.fingerprint is not None
        assert len(env.fingerprint) == 64
        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.28.0"
        assert env.kubernetes.nodeCount == 3
        assert env.runtime is not None
        assert env.runtime.containerRuntime == "containerd"

    def test_collect_environment_with_override(self, collector):
        """Test environment collection with overrides."""
        # Build expected override environment using builder
        expected_env = (
            default_environment_builder()
            .with_cluster("override-cluster")
            .with_fingerprint("b" * 64)
            .with_kubernetes(KubernetesBuilder().with_version("v1.27.0").with_node_count(5).build())
            .with_runtime(RuntimeBuilder().with_container_runtime("docker").build())
            .build()
        )

        # Convert to dict for override (as collector expects dict)
        # includes all fields with None
        override_dict = expected_env.model_dump()
        collector.set_override("environment", override_dict)

        env = collector.collect_environment()
        assert env.cluster == "override-cluster"
        assert env.fingerprint == "b" * 64
        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.27.0"
        assert env.kubernetes.nodeCount == 5
        assert env.runtime is not None
        assert env.runtime.containerRuntime == "docker"

    def test_collect_environment_caching(self, collector_with_config):
        """Test that environment is cached after first collection."""
        env1 = collector_with_config.collect_environment()
        env2 = collector_with_config.collect_environment()
        assert env1 is env2

    @patch("platform.system")
    @patch("perfeng.metadata.collector.psutil")
    def test_detect_node_info(self, mock_psutil, mock_platform, collector):
        """Test node information detection."""
        mock_platform.return_value = "Linux"
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.virtual_memory.return_value.total = 16 * (1024**3)
        mock_psutil.disk_usage.return_value.total = 100 * (1024**3)

        node_info = collector._detect_node_info()

        assert node_info["os"] == "Linux"
        assert node_info["resources"]["cpu_cores"] == 8
        assert node_info["resources"]["memory_total_gb"] == 16.0

    def test_generate_fingerprint(self, collector):
        """Test fingerprint generation."""
        fingerprint = collector._generate_fingerprint(
            cluster_name="test-cluster",
            k8s_version="v1.28.0",
            node_os="linux",
            container_runtime="containerd",
        )

        assert len(fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in fingerprint)

        # Same inputs -> same fingerprint
        fingerprint2 = collector._generate_fingerprint(
            cluster_name="test-cluster",
            k8s_version="v1.28.0",
            node_os="linux",
            container_runtime="containerd",
        )
        assert fingerprint == fingerprint2

        # Different inputs -> different fingerprint
        fingerprint3 = collector._generate_fingerprint(
            cluster_name="different-cluster",
            k8s_version="v1.28.0",
            node_os="linux",
            container_runtime="containerd",
        )
        assert fingerprint != fingerprint3

    def test_generate_fingerprint_with_exclusions(self, collector):
        """Test fingerprint generation with exclusions."""
        collector.config["fingerprint_excludes"] = ["test-cluster"]

        fingerprint = collector._generate_fingerprint(
            cluster_name="test-cluster",
            k8s_version="v1.28.0",
            node_os="linux",
            container_runtime="containerd",
        )

        assert len(fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in fingerprint)

    def test_test_metadata_collection(self):
        """Test collecting complete test metadata."""
        collector = MetadataCollector()

        # Pass custom fields via featureFlags or notes if needed
        metadata = collector.collect_test_metadata(
            test_name="test-perf-1",
            status="running",
            test_profile="load-test",  # will map to Profile.regression (default)
            tags=["performance", "load"],
            thresholds={"p95": 100},
            featureFlags={"tags": ["performance", "load"], "thresholds": {"p95": 100}},
            notes="script.py",  # store test_script in notes
        )

        # Run fields
        assert metadata.run.suite == "test-perf-1"
        assert metadata.run.status == RunStatus.RUNNING
        # profile defaults to regression because "load-test" not in enum
        assert metadata.run.profile == Profile.regression

        # Custom metadata stored in featureFlags
        assert metadata.candidate.featureFlags is not None
        assert metadata.candidate.featureFlags["tags"] == ["performance", "load"]
        assert metadata.candidate.featureFlags["thresholds"] == {"p95": 100}
        assert metadata.run.notes == "script.py"

        # Environment is now RunEnvironment, not EnvironmentSpecification
        assert isinstance(metadata.environment, RunEnvironment)

    def test_collect_test_metadata_with_overrides(self, collector):
        """Test test metadata collection with overrides."""
        collector.set_override(
            "test_metadata",
            {"run.suite": "override-name", "run.status": RunStatus.COMPLETED},
        )
        metadata = collector.collect_test_metadata(test_name="original-name", status="pending")
        assert metadata.run.suite == "override-name"
        assert metadata.run.status == RunStatus.COMPLETED

    def test_collect_test_metadata_with_environment(self, collector_with_config):
        """Test that test metadata includes environment."""
        metadata = collector_with_config.collect_test_metadata(test_name="load-test")
        assert isinstance(metadata.environment, RunEnvironment)
        assert metadata.environment.cluster == "test-cluster"
        assert metadata.environment.kubernetesVersion == "v1.28.0"

    @patch("subprocess.run")
    def test_auto_detect_kubernetes(self, mock_run, collector):
        """Test auto-detection of Kubernetes environment."""

        def side_effect(*args, **kwargs):
            cmd = args[0] if args else []
            cmd_str = " ".join(cmd)
            if "cluster-info" in cmd_str:
                return Mock(returncode=0, stdout="", stderr="")
            elif "current-context" in cmd_str:
                return Mock(returncode=0, stdout="test-context\n", stderr="")
            elif "version" in cmd_str:
                return Mock(
                    returncode=0, stdout='{"serverVersion":{"gitVersion":"v1.28.0"}}', stderr=""
                )
            elif "get nodes" in cmd_str:
                return Mock(
                    returncode=0,
                    stdout=json.dumps(
                        {
                            "items": [
                                {
                                    "metadata": {"name": "node1"},
                                    "status": {"capacity": {"cpu": "4", "memory": "16Gi"}},
                                },
                                {
                                    "metadata": {"name": "node2"},
                                    "status": {"capacity": {"cpu": "4", "memory": "16Gi"}},
                                },
                                {
                                    "metadata": {"name": "node3"},
                                    "status": {"capacity": {"cpu": "4", "memory": "16Gi"}},
                                },
                            ]
                        }
                    ),
                    stderr="",
                )
            else:
                return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        collector.config["auto_detect"] = True
        collector._environment_cache = None

        env = collector.collect_environment()
        assert env.cluster == "test-context"
        assert env.kubernetes is not None
        assert env.kubernetes.node_count == 3

    @patch("subprocess.run")
    def test_auto_detect_kubectl_not_available(self, mock_run, collector):
        mock_run.side_effect = FileNotFoundError("kubectl not found")
        collector.config["auto_detect"] = True
        collector._environment_cache = None

        env = collector.collect_environment()
        # The collector should fall back to defaults
        assert env.cluster is not None
        assert len(env.fingerprint) == 64
        assert env.kubernetes.version == "0.0.0"  # fallback
        assert env.kubernetes.nodeCount == 1  # default

    def test_deep_merge(self, collector):
        """Test deep merge of configuration dictionaries."""
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"c": 4}, "e": 5}

        result = collector._deep_merge(base, override)
        assert result["a"] == 1
        assert result["b"]["c"] == 4
        assert result["b"]["d"] == 3
        assert result["e"] == 5


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_metadata_collector(self):
        """Test factory function for metadata collector."""
        collector = get_metadata_collector()
        assert isinstance(collector, MetadataCollector)

        # With config path
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"auto_detect": False}, f)
            config_path = f.name

        collector = get_metadata_collector(config_path)
        assert collector.config["auto_detect"] is False
        Path(config_path).unlink()

    def test_collect_run_metadata(self):
        metadata_dict = collect_run_metadata(test_name="quick-test", tags=["quick"])
        assert isinstance(metadata_dict, dict)
        assert metadata_dict["run"]["suite"] == "quick-test"
        # tags are stored in candidate.featureFlags
        assert "tags" in metadata_dict["candidate"]["featureFlags"]
        assert metadata_dict["candidate"]["featureFlags"]["tags"] == ["quick"]
        assert "fingerprint" in metadata_dict["environment"]


class TestSchemaIntegration:
    """Test integration with generated schema models using builders."""

    def test_environment_specification_validation(self):
        """Test that EnvironmentSpecification validates correctly."""
        env = (
            default_environment_builder()
            .with_kubernetes(default_kubernetes_builder().build())
            .with_runtime(default_runtime_builder().build())
            .build()
        )
        assert env.cluster == "test-cluster"
        assert env.fingerprint == "a" * 64

    def test_environment_specification_invalid_fingerprint(self):
        """Test that invalid fingerprint raises validation error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            EnvironmentBuilder().with_cluster("test").with_fingerprint("not-a-hex-string").build()

    def test_node_pool_model(self):
        """Test NodePool model."""
        node_pool = (
            default_node_pool_builder()
            .with_name("pool-1")
            .with_node_model("m5.xlarge")
            .with_cpu_architecture(CpuArchitecture.amd64)
            .with_cpu_count(4)
            .with_memory_gi_b(16.0)
            .build()
        )
        assert node_pool.name == "pool-1"
        assert node_pool.cpuArchitecture == CpuArchitecture.amd64
        assert node_pool.cpuCount == 4

    def test_environment_deserialization(self):
        """Test deserialization from JSON using builders."""
        env = default_environment_builder().build()
        json_str = env.model_dump_json()
        reconstructed = EnvironmentSpecification.model_validate_json(json_str)
        assert reconstructed.cluster == env.cluster
        assert reconstructed.fingerprint == env.fingerprint

    def test_environment_to_dict(self):
        """Test conversion to dictionary with model_dump."""
        env = (
            default_environment_builder()
            .with_kubernetes(default_kubernetes_builder().build())
            .with_runtime(default_runtime_builder().build())
            .build()
        )
        as_dict = env.model_dump(exclude_none=True)
        assert as_dict["cluster"] == "test-cluster"
        assert "kubernetes" in as_dict
        assert "runtime" in as_dict
        # Not provided → should be excluded
        assert "compatibility" not in as_dict

    def test_model_copy(self):
        """Test copying models."""
        env = default_environment_builder().build()
        env_copy = env.model_copy()
        assert env_copy is not env
        assert env_copy.cluster == env.cluster
        assert env_copy.fingerprint == env.fingerprint

        # Update copy
        env_updated = env.model_copy(update={"cluster": "new-cluster"})
        assert env_updated.cluster == "new-cluster"
        assert env_updated.fingerprint == env.fingerprint
