"""
Unit tests for the metadata collector using the new typed architecture.
"""

import pytest

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import Profile
from perfeng.generated.run_metadata import Status as RunStatus
from perfeng.metadata.collector import (
    MetadataCollector,
    MetadataInput,
    MetadataOverrides,
    collect_run_metadata,
    get_metadata_collector,
)

pytestmark = pytest.mark.metadata


class TestMetadataCollector:
    """Test cases for MetadataCollector."""

    def test_init_default(self):
        """Test initialization with default settings."""
        collector = MetadataCollector()  # loads default config
        assert collector.config.auto_detect is True
        assert collector.config.timeout_seconds == 30

    def test_init_with_config(self, collector_config):
        """Test initialization with a typed config."""
        collector = MetadataCollector(config=collector_config)
        assert collector.config.auto_detect is False

    def test_collect_environment_no_autodetect(self, collector):
        """Environment collection with auto_detect off uses local only."""
        env = collector.collect_environment()
        assert isinstance(env, EnvironmentSpecification)
        assert env.cluster == "local"  # fallback
        assert len(env.fingerprint) == 64

    def test_collect_environment_caching(self, collector):
        """Environment is cached after first collection."""
        env1 = collector.collect_environment()
        env2 = collector.collect_environment()
        assert env1 is env2

    def test_collect_environment_with_overrides(self, collector):
        """Environment collection with overrides applied."""
        overrides = MetadataOverrides(
            cluster_name="override-cluster",
            kubernetes_version="v1.27.0",
            node_count=5,
            container_runtime="docker",
        )
        env = collector.collect_environment(overrides=overrides)
        assert env.cluster == "override-cluster"
        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.27.0"
        assert env.kubernetes.nodeCount == 5
        assert env.runtime is not None
        assert env.runtime.containerRuntime == "docker"

    def test_collect_test_metadata(self, collector):
        """Collecting test metadata with typed parameters."""
        metadata = collector.collect_test_metadata(
            test_name="test-perf-1",
            status="running",
            test_metadata=MetadataInput(
                test_profile="smoke",
                tool="k6",
                tool_version="0.45.0",
                scenario="scenario.js",
                git_sha="a" * 40,
                version="1.0.0",
            ),
        )
        assert metadata.run.suite == "test-perf-1"
        assert metadata.run.status == RunStatus.RUNNING
        assert metadata.run.profile == Profile.smoke
        assert metadata.test.tool.value == "k6"
        assert metadata.environment is not None

    def test_collect_test_metadata_with_environment_overrides(self, collector):
        """Test metadata collection with environment overrides."""
        metadata = collector.collect_test_metadata(
            test_name="load-test",
            status="created",
            environment_overrides=MetadataOverrides(cluster_name="test-cluster"),
        )
        assert metadata.environment.cluster == "test-cluster"

    def test_collect_run_metadata_dict(self):
        """Convenience function returns a dict."""
        result = collect_run_metadata(test_name="quick-test")
        assert isinstance(result, dict)
        assert result["run"]["suite"] == "quick-test"
        assert "fingerprint" in result["environment"]

    def test_get_metadata_collector(self):
        """Factory function returns a MetadataCollector."""
        collector = get_metadata_collector()
        assert isinstance(collector, MetadataCollector)
