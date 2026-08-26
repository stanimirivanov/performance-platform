"""
Tests for the metadata collector.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.metadata.collector import MetadataCollector
from perfeng.metadata.config_loader import ConfigLoader, create_collector_for_environment


class TestMetadataCollector:
    """Test cases for MetadataCollector."""

    def test_init_with_config(self):
        """Test initialization with configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"auto_detect": False}, f)
            config_path = f.name

        collector = MetadataCollector(config_path)
        assert collector.config["auto_detect"] is False

        Path(config_path).unlink()

    def test_collect_environment_from_config(self):
        """Test collecting environment from config only."""
        config = {
            "auto_detect": False,
            "environment_config": {
                "cluster": "test-cluster",
                "kubernetes": {"version": "v1.28.0", "nodeCount": 3},
                "runtime": {
                    "containerRuntime": "containerd",
                    "cni": "calico",
                    "storageClass": "standard",
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        collector = MetadataCollector(config_path)
        env = collector.collect_environment()

        assert env.cluster == "test-cluster"
        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.28.0"
        assert env.kubernetes.node_count == 3
        assert env.runtime is not None
        assert env.runtime.container_runtime == "containerd"

        Path(config_path).unlink()

    @patch("subprocess.run")
    def test_auto_detect_kubernetes(self, mock_run):
        """Test auto-detection of Kubernetes environment."""
        # Mock kubectl responses
        mock_run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),  # cluster-info
            Mock(returncode=0, stdout="test-context", stderr=""),  # current-context
            Mock(
                returncode=0,
                stdout=json.dumps(
                    {"items": [{"metadata": {"name": "node1"}}, {"metadata": {"name": "node2"}}]}
                ),
                stderr="",
            ),  # get nodes
        ]

        config = {"auto_detect": True, "timeout_seconds": 30, "environment_config": {}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        collector = MetadataCollector(config_path)
        env = collector.collect_environment()

        assert env.cluster == "test-context"
        assert env.kubernetes is not None
        assert env.kubernetes.node_count == 2

        Path(config_path).unlink()

    def test_manual_override(self):
        """Test manual override of environment values."""
        collector = MetadataCollector()

        # Set override
        override_env = {
            "cluster": "override-cluster",
            "fingerprint": "a" * 64,
            "kubernetes": {"version": "v1.27.0", "nodeCount": 5},
        }
        collector.set_override("environment", override_env)

        env = collector.collect_environment()
        assert env.cluster == "override-cluster"
        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.27.0"

    def test_test_metadata_collection(self):
        """Test collecting complete test metadata."""
        collector = MetadataCollector()

        metadata = collector.collect_test_metadata(
            test_name="test-perf-1",
            status="running",
            test_script="script.py",
            test_profile="load-test",
            tags=["performance", "load"],
            thresholds={"p95": 100},
        )

        assert metadata.test_name == "test-perf-1"
        assert metadata.status == "running"
        assert metadata.tags == ["performance", "load"]
        assert metadata.thresholds == {"p95": 100}
        assert isinstance(metadata.environment, EnvironmentSpecification)

    def test_fingerprint_generation(self):
        """Test fingerprint generation."""
        collector = MetadataCollector()

        fingerprint = collector._generate_fingerprint(
            cluster_name="test-cluster",
            k8s_version="v1.28.0",
            node_os="linux",
            container_runtime="containerd",
        )

        # Fingerprint should be a 64-character hex string
        assert len(fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in fingerprint)

    def test_fingerprint_with_exclusions(self):
        """Test fingerprint generation with exclusions."""
        config = {"fingerprint_excludes": ["test-cluster", "v1.28.0"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        collector = MetadataCollector(config_path)

        fingerprint1 = collector._generate_fingerprint(
            cluster_name="test-cluster",
            k8s_version="v1.28.0",
            node_os="linux",
            container_runtime="containerd",
        )

        fingerprint2 = collector._generate_fingerprint(
            cluster_name="prod-cluster",
            k8s_version="v1.28.0",
            node_os="linux",
            container_runtime="containerd",
        )

        # Fingerprints should be different because 'test-cluster' was excluded
        assert fingerprint1 != fingerprint2

        Path(config_path).unlink()


class TestConfigLoader:
    """Test cases for ConfigLoader."""

    def test_environment_detection(self):
        """Test automatic environment detection."""
        loader = ConfigLoader("local")
        assert loader.env_type == "local"

    @patch.dict(os.environ, {"PERFENG_ENV": "prod"})
    def test_environment_detection_from_env(self):
        """Test environment detection from environment variable."""
        loader = ConfigLoader()
        assert loader.env_type == "prod"

    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "PERFENG_CLUSTER_NAME": "env-cluster",
                "PERFENG_AUTO_DETECT": "false",
                "PERFENG_TIMEOUT": "60",
            },
        ):
            loader = ConfigLoader("local")
            env_config = loader.load_environment_variables()

            assert env_config["environment_config"]["cluster"] == "env-cluster"
            assert env_config["auto_detect"] is False
            assert env_config["timeout_seconds"] == 60

    def test_create_collector_for_environment(self):
        """Test creating a collector for a specific environment."""
        collector = create_collector_for_environment("local")
        assert collector is not None
        assert hasattr(collector, "collect_environment")


class TestIntegration:
    """Integration tests for the full metadata collection flow."""

    def test_end_to_end_collection(self):
        """Test end-to-end metadata collection."""
        # Create a collector with test config
        config = {
            "auto_detect": False,
            "environment_config": {
                "cluster": "integration-test",
                "kubernetes": {"version": "v1.28.0", "nodeCount": 1},
                "runtime": {
                    "containerRuntime": "docker",
                    "cni": "bridge",
                    "storageClass": "standard",
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        collector = MetadataCollector(config_path)

        # Collect metadata
        metadata = collector.collect_test_metadata(
            test_name="integration-test", status="running", tags=["integration"]
        )

        # Verify results
        assert metadata.test_name == "integration-test"
        assert metadata.status == "running"
        assert metadata.environment.cluster == "integration-test"
        assert metadata.environment.kubernetes is not None
        assert metadata.environment.kubernetes.version == "v1.28.0"

        # Verify fingerprint format
        assert len(metadata.environment.fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in metadata.environment.fingerprint)

        Path(config_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
