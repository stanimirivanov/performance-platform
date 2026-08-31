"""
Tests for MetadataCollector and convenience functions.
"""

from unittest.mock import Mock

import pytest

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.metadata.builders.config import (
    CandidateConfig,
    ExecutorConfig,
    RunConfig,
    RunMetadataBuildConfig,
)
from perfeng.metadata.collector import (
    MetadataCollector,
    collect_run_metadata,
    get_metadata_collector,
)
from perfeng.metadata.config import CollectorConfig
from perfeng.metadata.config.models import ClusterConfig, KubernetesConfig, RuntimeConfig
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


@pytest.fixture
def sample_run_metadata_config():
    return RunMetadataBuildConfig(
        test_name="checkout-api",
        status="running",
        run=RunConfig(profile="smoke", trigger="ci"),
        test=ExecutorConfig(
            tool="k6",
            tool_version="0.45.0",
            test_type="api",
            scenario="checkout-flow",
        ),
        candidate=CandidateConfig(git_sha="a" * 40, version="1.0.0"),
    )


class TestMetadataCollector:
    def test_init_default(self):
        collector = MetadataCollector()
        assert collector.config.auto_detect is True

    def test_init_with_config(self, config_no_detect):
        collector = MetadataCollector(config=config_no_detect)
        assert collector.config.auto_detect is False

    def test_collect_environment_no_autodetect(self, config_no_detect, fake_detectors):
        local, _ = fake_detectors
        collector = MetadataCollector(config=config_no_detect, local_detector=local)
        env = collector.collect_environment()
        assert isinstance(env, EnvironmentSpecification)
        assert env.cluster == "local"
        assert len(env.fingerprint) == 64

    def test_collect_environment_with_auto_detect(self, fake_detectors):
        local, k8s = fake_detectors
        config = CollectorConfig(auto_detect=True, timeout_seconds=30, fingerprint_excludes=())
        collector = MetadataCollector(config=config, local_detector=local, k8s_detector=k8s)
        env = collector.collect_environment()
        assert env.cluster == "test-cluster"
        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.28.0"

    def test_collect_environment_with_config_override(self, config_no_detect, fake_detectors):
        local, _ = fake_detectors
        collector = MetadataCollector(config=config_no_detect, local_detector=local)

        override_config = CollectorConfig(
            auto_detect=False,
            timeout_seconds=30,
            fingerprint_excludes=(),
            cluster=ClusterConfig(name="override-cluster", type=None),
            kubernetes=KubernetesConfig(version="v1.27.0", node_count=5, node_pools=None),
            runtime=RuntimeConfig(
                container_runtime="docker",
                cni=None,
                storage_class=None,
                kernel=None,
            ),
        )
        env = collector.collect_environment(config_override=override_config)
        assert env.cluster == "override-cluster"
        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.27.0"
        assert env.kubernetes.nodeCount == 5
        assert env.runtime is not None
        assert env.runtime.containerRuntime == "docker"

    def test_collect_test_metadata(
        self,
        config_no_detect,
        fake_detectors,
        sample_run_metadata_config,
    ):
        local, _ = fake_detectors
        collector = MetadataCollector(config=config_no_detect, local_detector=local)

        metadata = collector.collect_test_metadata(sample_run_metadata_config)
        assert metadata.run.suite == "checkout-api"
        assert metadata.test.tool.value == "k6"
        assert metadata.candidate.gitSha == "a" * 40

    def test_collect_run_metadata_dict(self, sample_run_metadata_config):
        result = collect_run_metadata(sample_run_metadata_config)
        assert isinstance(result, dict)
        assert result["run"]["suite"] == "checkout-api"
        assert "fingerprint" in result["environment"]

    def test_get_metadata_collector(self):
        collector = get_metadata_collector()
        assert isinstance(collector, MetadataCollector)
