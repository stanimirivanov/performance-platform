"""
Integration tests for the complete metadata flow.
"""

import pytest

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import PerformanceRunMetadata, Status
from perfeng.metadata.builders.config import (
    CandidateConfig,
    ExecutorConfig,
    RunConfig,
    RunMetadataBuildConfig,
)
from perfeng.metadata.collector import MetadataCollector
from perfeng.metadata.config import CollectorConfig
from perfeng.metadata.config.models import ClusterConfig, KubernetesConfig, RuntimeConfig


@pytest.mark.integration
class TestMetadataFlow:
    """End-to-end integration tests using typed config."""

    def _make_collector(
        self,
        cluster: str = "test-cluster",
        k8s_version: str = "v1.28.0",
        node_count: int = 3,
        container_runtime: str = "containerd",
        cni: str = "calico",
        storage_class: str = "standard",
        kernel: str = "5.15.0",
    ) -> MetadataCollector:
        """Create a MetadataCollector with a fixed, non-detecting config."""
        config = CollectorConfig(
            auto_detect=False,
            timeout_seconds=30,
            fingerprint_excludes=(),
            cluster=ClusterConfig(name=cluster, type=None),
            kubernetes=KubernetesConfig(
                version=k8s_version,
                node_count=node_count,
                node_pools=None,
            ),
            runtime=RuntimeConfig(
                container_runtime=container_runtime,
                cni=cni,
                storage_class=storage_class,
                kernel=kernel,
            ),
        )
        return MetadataCollector(config=config)

    def test_complete_collection_flow(self):
        """Test complete metadata collection flow."""
        collector = self._make_collector()

        env = collector.collect_environment()
        assert isinstance(env, EnvironmentSpecification)
        assert env.cluster == "test-cluster"
        assert len(env.fingerprint) == 64

        assert env.kubernetes is not None
        assert env.runtime is not None
        assert env.kubernetes.version == "v1.28.0"
        assert env.kubernetes.nodeCount == 3

        # Build run metadata config
        run_config = RunMetadataBuildConfig(
            test_name="integration-test",
            status="RUNNING",
            run=RunConfig(profile="smoke", trigger="manual"),
            test=ExecutorConfig(tool="k6", tool_version="0.45.0", scenario="flow.js"),
            candidate=CandidateConfig(
                git_sha="a" * 40,
                version="1.0.0",
                feature_flags={"tags": ["integration"], "thresholds": {"p95": 100}},
            ),
        )

        metadata = collector.collect_test_metadata(run_config)

        assert isinstance(metadata, PerformanceRunMetadata)
        assert metadata.run.suite == "integration-test"
        assert metadata.run.status == Status.RUNNING
        assert metadata.environment.cluster == "test-cluster"
        assert metadata.candidate.featureFlags is not None
        assert "tags" in metadata.candidate.featureFlags
        assert "thresholds" in metadata.candidate.featureFlags

    def test_serialization_roundtrip(self):
        """Test that metadata can be serialized and deserialized."""
        collector = self._make_collector()
        env = collector.collect_environment()

        json_str = env.model_dump_json()
        env2 = EnvironmentSpecification.model_validate_json(json_str)

        assert env2.cluster == env.cluster
        assert env2.fingerprint == env.fingerprint
        assert env.kubernetes is not None
        assert env2.kubernetes is not None
        assert env2.kubernetes.version == env.kubernetes.version

    def test_environment_comparison(self):
        """Test comparing different environments."""
        env1 = self._make_collector(cluster="cluster-a").collect_environment()
        env2 = self._make_collector(cluster="cluster-b").collect_environment()

        assert env1.fingerprint != env2.fingerprint

    def test_full_run_metadata_structure(self):
        """Test that the collector can produce the full run metadata structure."""
        collector = self._make_collector()
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
