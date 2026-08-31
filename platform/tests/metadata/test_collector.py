"""
Tests for MetadataCollector and convenience functions.
"""

from unittest.mock import Mock

import pytest

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.metadata.collector import (
    MetadataCollector,
    MetadataInput,
    MetadataOverrides,
    collect_run_metadata,
    get_metadata_collector,
)
from perfeng.metadata.config import CollectorConfig
from perfeng.metadata.detectors import (
    ClusterInfo,
    ClusterType,
    KubernetesClusterDetector,
    LocalNodeDetector,
    NodeInfo,
    NodeResources,
)


@pytest.fixture
def sample_node_info():
    return NodeInfo(
        os="Linux",
        kernel="5.15.0",
        architecture="x86_64",
        resources=NodeResources(cpu_cores=8, memory_total_gb=16.0, disk_total_gb=100.0),
    )


@pytest.fixture
def sample_cluster_info():
    return ClusterInfo(name="test-cluster", type=ClusterType.KUBERNETES, node_count=3)


@pytest.fixture
def config_no_detect():
    return CollectorConfig(auto_detect=False, timeout_seconds=30, fingerprint_excludes=())


@pytest.fixture
def fake_detectors(sample_node_info, sample_cluster_info):
    local = Mock(spec=LocalNodeDetector)
    local.detect.return_value = sample_node_info
    k8s = Mock(spec=KubernetesClusterDetector)
    k8s.detect.return_value = sample_cluster_info
    k8s.detect_version.return_value = "v1.28.0"
    k8s.detect_node_pools.return_value = None
    k8s.detect_container_runtime.return_value = "containerd"
    k8s.detect_cni.return_value = "calico"
    k8s.detect_storage_class.return_value = "standard"
    return local, k8s


class TestMetadataCollector:
    def test_init_default(self):
        collector = MetadataCollector()
        assert collector.config.auto_detect is True

    def test_init_with_config(self, config_no_detect):
        collector = MetadataCollector(config=config_no_detect)
        assert collector.config.auto_detect is False

    def test_collect_environment_no_autodetect(self, config_no_detect, fake_detectors):
        local, _ = fake_detectors
        collector = MetadataCollector(
            config=config_no_detect,
            local_detector=local,
        )
        env = collector.collect_environment()
        assert isinstance(env, EnvironmentSpecification)
        assert env.cluster == "local"
        assert len(env.fingerprint) == 64

    def test_collect_environment_with_auto_detect(self, fake_detectors):
        local, k8s = fake_detectors
        config = CollectorConfig(auto_detect=True, timeout_seconds=30, fingerprint_excludes=())
        collector = MetadataCollector(
            config=config,
            local_detector=local,
            k8s_detector=k8s,
        )
        env = collector.collect_environment()
        assert env.cluster == "test-cluster"

        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.28.0"

    def test_collect_environment_with_overrides(self, config_no_detect, fake_detectors):
        local, _ = fake_detectors
        collector = MetadataCollector(config=config_no_detect, local_detector=local)
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

    def test_collect_test_metadata(self, config_no_detect, fake_detectors):
        local, _ = fake_detectors
        collector = MetadataCollector(config=config_no_detect, local_detector=local)
        metadata_input = MetadataInput(
            test_profile="smoke",
            tool="k6",
            tool_version="0.45.0",
            scenario="checkout-flow",
            git_sha="a" * 40,
            version="1.0.0",
        )
        metadata = collector.collect_test_metadata(
            test_name="checkout-api",
            status="running",
            test_metadata=metadata_input,
        )
        assert metadata.run.suite == "checkout-api"
        assert metadata.test.tool.value == "k6"
        assert metadata.candidate.gitSha == "a" * 40

    def test_collect_test_metadata_with_env_overrides(self, config_no_detect, fake_detectors):
        local, _ = fake_detectors
        collector = MetadataCollector(config=config_no_detect, local_detector=local)
        metadata = collector.collect_test_metadata(
            test_name="load-test",
            status="created",
            environment_overrides=MetadataOverrides(cluster_name="test-cluster"),
        )
        assert metadata.environment.cluster == "test-cluster"

    def test_collect_run_metadata_dict(self):
        result = collect_run_metadata(test_name="quick-test")
        assert isinstance(result, dict)
        assert result["run"]["suite"] == "quick-test"
        assert "fingerprint" in result["environment"]

    def test_get_metadata_collector(self):
        collector = get_metadata_collector()
        assert isinstance(collector, MetadataCollector)
