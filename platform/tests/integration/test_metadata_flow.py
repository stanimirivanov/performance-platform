# platform/tests/integration/test_metadata_flow.py
"""
Integration tests for the complete metadata flow.
"""

from pathlib import Path

import pytest
import yaml

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import PerformanceRunMetadata, Status
from perfeng.metadata.collector import MetadataCollector


@pytest.mark.integration
class TestMetadataFlow:
    """End-to-end integration tests."""

    def _create_temp_config(self, tmp_path: Path, config_override: dict | None = None) -> Path:
        """Helper to create a temporary config file."""
        default_config = {
            "auto_detect": False,
            "timeout_seconds": 30,
            "fingerprint_excludes": [],
            "environment_config": {
                "cluster": "test-cluster",
                "kubernetes": {"version": "v1.28.0", "nodeCount": 3},
                "runtime": {
                    "containerRuntime": "containerd",
                    "cni": "calico",
                    "storageClass": "standard",
                    "kernel": "5.15.0",
                },
            },
        }
        if config_override:
            # Deep merge (simplified)
            import copy

            config = copy.deepcopy(default_config)
            for key, value in config_override.items():
                if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                    config[key].update(value)
                else:
                    config[key] = value
        else:
            config = default_config

        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return config_path

    def test_complete_collection_flow(self, tmp_path):
        """Test complete metadata collection flow."""
        config_path = self._create_temp_config(tmp_path)
        collector = MetadataCollector(config_path)

        env = collector.collect_environment()
        assert isinstance(env, EnvironmentSpecification)
        assert env.cluster == "test-cluster"
        assert len(env.fingerprint) == 64

        # Check kubernetes is not None before accessing attributes
        assert env.kubernetes is not None, "Kubernetes info should be present"
        assert env.runtime is not None, "Runtime info should be present"

        # Now safe to access attributes
        assert env.kubernetes.version == "v1.28.0"
        assert env.kubernetes.nodeCount == 3

        # Collect test metadata
        metadata = collector.collect_test_metadata(
            test_name="integration-test",
            status="RUNNING",
            tags=["integration"],
            thresholds={"p95": 100},
        )

        assert isinstance(metadata, PerformanceRunMetadata)
        assert metadata.run.suite == "integration-test"
        assert metadata.run.status == Status.RUNNING
        assert metadata.environment.cluster == "test-cluster"
        assert metadata.candidate.featureFlags is not None
        assert "tags" in metadata.candidate.featureFlags
        assert "thresholds" in metadata.candidate.featureFlags

    def test_serialization_roundtrip(self, tmp_path):
        """Test that metadata can be serialized and deserialized."""
        config_path = self._create_temp_config(tmp_path)
        collector = MetadataCollector(config_path)
        env = collector.collect_environment()

        # Serialize to JSON
        json_str = env.model_dump_json()
        env2 = EnvironmentSpecification.model_validate_json(json_str)

        assert env2.cluster == env.cluster
        assert env2.fingerprint == env.fingerprint
        assert env.kubernetes is not None
        assert env2.kubernetes is not None
        assert env2.kubernetes.version == env.kubernetes.version

    def test_environment_comparison(self, tmp_path):
        """Test comparing different environments."""
        config1_path = self._create_temp_config(tmp_path)
        collector1 = MetadataCollector(config1_path)
        env1 = collector1.collect_environment()

        config2_path = self._create_temp_config(
            tmp_path, {"environment_config": {"cluster": "different-cluster"}}
        )
        collector2 = MetadataCollector(config2_path)
        env2 = collector2.collect_environment()

        assert env1.fingerprint != env2.fingerprint

    def test_full_run_metadata_structure(self, tmp_path):
        """Test that the collector can produce the full run metadata structure."""
        config_path = self._create_temp_config(tmp_path)
        collector = MetadataCollector(config_path)
        env = collector.collect_environment()

        run_metadata = {
            "run_id": "perf-20240115-143022-ab12cd34",
            "environment": {
                "cluster": env.cluster,
                "kubernetes_version": env.kubernetes.version if env.kubernetes else None,
                "node_count": env.kubernetes.nodeCount if env.kubernetes else 1,
                "fingerprint": env.fingerprint,
                "runtime": {
                    "container_runtime": env.runtime.containerRuntime if env.runtime else None,
                    "cni": env.runtime.cni if env.runtime else None,
                    "kernel": env.runtime.kernel if env.runtime else None,
                },
            },
        }

        assert "run_id" in run_metadata
        assert "environment" in run_metadata
        assert run_metadata["environment"]["fingerprint"] == env.fingerprint
