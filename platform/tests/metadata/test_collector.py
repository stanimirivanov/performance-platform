"""
Unit tests for the metadata collector.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from perfeng.generated.environment import CpuArchitecture, EnvironmentSpecification
from perfeng.metadata.collector import (
    MetadataCollector,
    TestMetadata,
    collect_run_metadata,
    get_metadata_collector,
)


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

    def test_init_with_nonexistent_config(self):
        """Test initialization with nonexistent config file."""
        collector = MetadataCollector("/nonexistent/path/config.yaml")
        assert collector.config["auto_detect"] is True
        # Should use defaults
        assert "environment_config" in collector.config

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
        assert env.kubernetes.node_count == 3

        assert env.runtime is not None
        assert env.runtime.container_runtime == "containerd"
        assert env.runtime.cni == "calico"
        assert env.runtime.storage_class == "standard"
        assert env.runtime.kernel == "5.15.0"

    def test_collect_environment_with_override(self, collector):
        """Test environment collection with overrides."""
        override_env = {
            "cluster": "override-cluster",
            "fingerprint": "b" * 64,
            "kubernetes": {"version": "v1.27.0", "nodeCount": 5},
            "runtime": {"containerRuntime": "docker"},
        }
        collector.set_override("environment", override_env)

        env = collector.collect_environment()

        assert env.cluster == "override-cluster"
        assert env.fingerprint == "b" * 64
        assert env.kubernetes.version == "v1.27.0"
        assert env.kubernetes.node_count == 5
        assert env.runtime.container_runtime == "docker"

    def test_collect_environment_caching(self, collector_with_config):
        """Test that environment is cached after first collection."""
        env1 = collector_with_config.collect_environment()
        env2 = collector_with_config.collect_environment()

        # Should return the same object (cached)
        assert env1 is env2
        assert collector_with_config._environment_cache is not None

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
        assert node_info["resources"]["disk_total_gb"] == 100.0

    def test_generate_fingerprint(self, collector):
        """Test fingerprint generation."""
        fingerprint = collector._generate_fingerprint(
            cluster_name="test-cluster",
            k8s_version="v1.28.0",
            node_os="linux",
            container_runtime="containerd",
        )

        # Should be a 64-character hex string
        assert len(fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in fingerprint)

        # Same inputs should generate same fingerprint
        fingerprint2 = collector._generate_fingerprint(
            cluster_name="test-cluster",
            k8s_version="v1.28.0",
            node_os="linux",
            container_runtime="containerd",
        )
        assert fingerprint == fingerprint2

        # Different inputs should generate different fingerprints
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

        # Should not include 'test-cluster' in fingerprint
        # Just verify it produces a valid hash
        assert len(fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in fingerprint)

    def test_collect_test_metadata(self, collector):
        """Test collecting complete test metadata."""
        metadata = collector.collect_test_metadata(
            test_name="load-test",
            status="running",
            test_script="load_test.py",
            test_profile="medium-load",
            thresholds={"p95": 100},
            tags=["performance"],
            trigger_type="ci",
        )

        assert isinstance(metadata, TestMetadata)
        assert metadata.test_name == "load-test"
        assert metadata.status == "running"
        assert metadata.test_script == "load_test.py"
        assert metadata.test_profile == "medium-load"
        assert metadata.thresholds == {"p95": 100}
        assert metadata.tags == ["performance"]
        assert metadata.trigger_type == "ci"
        assert isinstance(metadata.start_time, datetime)
        assert metadata.end_time is None
        assert metadata.duration_seconds is None

    def test_collect_test_metadata_with_overrides(self, collector):
        """Test test metadata collection with overrides."""
        collector.set_override(
            "test_metadata", {"test_name": "override-name", "status": "completed"}
        )

        metadata = collector.collect_test_metadata(test_name="original-name", status="pending")

        # Overrides should take precedence
        assert metadata.test_name == "override-name"
        assert metadata.status == "completed"

    def test_collect_test_metadata_with_environment(self, collector_with_config):
        """Test that test metadata includes environment."""
        metadata = collector_with_config.collect_test_metadata(test_name="load-test")

        assert isinstance(metadata.environment, EnvironmentSpecification)
        assert metadata.environment.cluster == "test-cluster"

    @patch("subprocess.run")
    def test_auto_detect_kubernetes(self, mock_run, collector):
        """Test auto-detection of Kubernetes environment."""
        # Setup mock responses
        mock_run.side_effect = [
            # cluster-info
            Mock(returncode=0, stdout="", stderr=""),
            # current-context
            Mock(returncode=0, stdout="test-context\n", stderr=""),
            # get nodes
            Mock(
                returncode=0,
                stdout=json.dumps(
                    {
                        "items": [
                            {"metadata": {"name": "node1"}},
                            {"metadata": {"name": "node2"}},
                            {"metadata": {"name": "node3"}},
                        ]
                    }
                ),
                stderr="",
            ),
        ]

        collector.config["auto_detect"] = True
        collector._environment_cache = None  # Clear cache

        env = collector.collect_environment()

        assert env.cluster == "test-context"
        assert env.kubernetes is not None
        assert env.kubernetes.node_count == 3

    @patch("subprocess.run")
    def test_auto_detect_kubectl_not_available(self, mock_run, collector):
        """Test auto-detection when kubectl is not available."""
        mock_run.side_effect = FileNotFoundError("kubectl not found")

        collector.config["auto_detect"] = True
        collector._environment_cache = None

        env = collector.collect_environment()

        # Should fall back to local detection
        assert env.cluster is not None
        assert env.kubernetes is not None

    def test_deep_merge(self, collector):
        """Test deep merge of configuration dictionaries."""
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"c": 4}, "e": 5}

        result = collector._deep_merge(base, override)

        assert result["a"] == 1
        assert result["b"]["c"] == 4  # Overridden
        assert result["b"]["d"] == 3  # Preserved
        assert result["e"] == 5  # Added


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
        """Test convenience function for collecting run metadata."""
        metadata_dict = collect_run_metadata(test_name="quick-test", tags=["quick"])

        assert isinstance(metadata_dict, dict)
        assert metadata_dict["test_name"] == "quick-test"
        assert metadata_dict["tags"] == ["quick"]
        assert "environment" in metadata_dict
        assert "fingerprint" in metadata_dict["environment"]


class TestSchemaIntegration:
    """Test integration with generated schema models."""

    def test_environment_specification_validation(self, sample_environment_dict):
        """Test that EnvironmentSpecification validates correctly."""
        env = EnvironmentSpecification(**sample_environment_dict)

        assert env.cluster == "test-cluster"
        assert env.fingerprint == "a" * 64
        assert env.kubernetes.version == "v1.28.0"
        assert env.runtime.container_runtime == "containerd"

    def test_environment_specification_invalid_fingerprint(self, sample_environment_dict):
        """Test that invalid fingerprint raises validation error."""
        from pydantic import ValidationError

        invalid = sample_environment_dict.copy()
        invalid["fingerprint"] = "not-a-hex-string"

        with pytest.raises(ValidationError):
            EnvironmentSpecification(**invalid)

    def test_environment_specification_to_json(self, sample_environment_dict):
        """Test serialization to JSON."""
        env = EnvironmentSpecification(**sample_environment_dict)
        json_str = env.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["cluster"] == "test-cluster"
        assert parsed["fingerprint"] == "a" * 64
        assert parsed["kubernetes"]["version"] == "v1.28.0"

    def test_node_pool_model(self):
        """Test NodePool model."""
        from perfeng.generated.environment import NodePool

        node_pool = NodePool(
            name="pool-1",
            node_model="m5.xlarge",
            cpu_architecture=CpuArchitecture.amd64,
            cpu_count=4,
            memory_gi_b=16.0,
        )

        assert node_pool.name == "pool-1"
        assert node_pool.cpu_architecture == CpuArchitecture.amd64
        assert node_pool.cpu_count == 4
        assert node_pool.memory_gi_b == 16.0
