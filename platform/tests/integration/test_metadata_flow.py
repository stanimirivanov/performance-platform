"""
Integration tests for the complete metadata flow.
"""

import json

import pytest

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.metadata.collector import MetadataCollector
from perfeng.metadata.config_loader import create_collector_for_environment


@pytest.mark.integration
class TestMetadataFlow:
    """End-to-end integration tests."""

    def test_complete_collection_flow(self, temp_config_file):
        """Test complete metadata collection flow."""
        collector = MetadataCollector(temp_config_file)

        # Collect environment
        env = collector.collect_environment()

        # Verify all fields
        assert isinstance(env, EnvironmentSpecification)
        assert env.cluster == "test-cluster"
        assert len(env.fingerprint) == 64
        assert env.kubernetes is not None
        assert env.runtime is not None

        # Collect test metadata
        metadata = collector.collect_test_metadata(
            test_name="integration-test", status="running", tags=["integration"]
        )

        # Verify metadata structure
        assert metadata.test_name == "integration-test"
        assert metadata.status == "running"
        assert metadata.tags == ["integration"]
        assert metadata.environment is env

    def test_serialization_roundtrip(self, temp_config_file):
        """Test that metadata can be serialized and deserialized."""
        collector = MetadataCollector(temp_config_file)
        env = collector.collect_environment()

        # Serialize to JSON
        json_str = env.model_dump_json()

        # Deserialize back
        parsed = json.loads(json_str)
        env2 = EnvironmentSpecification(**parsed)

        # Verify roundtrip
        assert env2.cluster == env.cluster
        assert env2.fingerprint == env.fingerprint
        assert env2.kubernetes.version == env.kubernetes.version

    def test_environment_comparison(self):
        """Test comparing different environments."""
        local = create_collector_for_environment("local")
        dev = create_collector_for_environment("dev")

        env_local = local.collect_environment()
        env_dev = dev.collect_environment()

        # Different environments should have different fingerprints
        # (unless configured identically)
        assert env_local.fingerprint != env_dev.fingerprint

    def test_full_run_metadata_structure(self):
        """Test that the collector can produce the full run metadata structure."""
        collector = create_collector_for_environment("local")
        env = collector.collect_environment()

        # Build full metadata as expected by the system
        run_metadata = {
            "run_id": "perf-20240115-143022-ab12cd34",
            "environment": {
                "cluster": env.cluster,
                "kubernetes_version": env.kubernetes.version if env.kubernetes else None,
                "node_count": env.kubernetes.node_count if env.kubernetes else 1,
                "fingerprint": env.fingerprint,
                "runtime": {
                    "container_runtime": env.runtime.container_runtime if env.runtime else None,
                    "cni": env.runtime.cni if env.runtime else None,
                    "kernel": env.runtime.kernel if env.runtime else None,
                },
            },
        }

        # Verify structure
        assert "run_id" in run_metadata
        assert "environment" in run_metadata
        assert run_metadata["environment"]["fingerprint"] == env.fingerprint
