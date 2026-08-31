"""
Tests for EnvironmentBuilder.
"""

from unittest.mock import Mock

import pytest

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.metadata.builders import EnvironmentBuilder
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
def fake_fingerprint_generator():
    gen = Mock()
    gen.generate.return_value = "a" * 64
    return gen


def make_config(auto_detect=True, **kwargs):
    return CollectorConfig(
        auto_detect=auto_detect,
        timeout_seconds=30,
        fingerprint_excludes=(),
        **kwargs,
    )


class TestEnvironmentBuilder:
    def test_build_with_no_detectors(self, sample_node_info, fake_fingerprint_generator):
        config = make_config(auto_detect=False)
        node_detector = Mock(spec=LocalNodeDetector)
        node_detector.detect.return_value = sample_node_info
        builder = EnvironmentBuilder(
            config=config,
            node_detector=node_detector,
            fingerprint_generator=fake_fingerprint_generator,
        )
        env = builder.build()
        assert isinstance(env, EnvironmentSpecification)
        assert env.cluster == "local"  # fallback
        assert env.kubernetes is None
        assert env.runtime is not None
        assert env.runtime.kernel == "5.15.0"
        assert env.fingerprint == "a" * 64

    def test_build_with_auto_detect(
        self, sample_node_info, sample_cluster_info, fake_fingerprint_generator
    ):
        config = make_config(auto_detect=True)
        node_detector = Mock(spec=LocalNodeDetector)
        node_detector.detect.return_value = sample_node_info
        cluster_detector = Mock(spec=KubernetesClusterDetector)
        cluster_detector.detect.return_value = sample_cluster_info
        cluster_detector.detect_version.return_value = "v1.28.0"
        cluster_detector.detect_node_pools.return_value = None
        cluster_detector.detect_container_runtime.return_value = "containerd"
        cluster_detector.detect_cni.return_value = "calico"
        cluster_detector.detect_storage_class.return_value = "standard"

        builder = EnvironmentBuilder(
            config=config,
            cluster_detector=cluster_detector,
            node_detector=node_detector,
            fingerprint_generator=fake_fingerprint_generator,
        )
        env = builder.build()
        assert env.cluster == "test-cluster"
        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.28.0"
        assert env.kubernetes.nodeCount == 3

        assert env.runtime is not None
        assert env.runtime.containerRuntime == "containerd"
        assert env.runtime.cni == "calico"
        assert env.runtime.storageClass == "standard"

    def test_build_uses_config_overrides(self, sample_node_info, fake_fingerprint_generator):
        config = make_config(
            auto_detect=False,
            cluster=type("ClusterConfig", (), {"name": "override-cluster", "type": None})(),
            kubernetes=type(
                "KubernetesConfig", (), {"version": "v1.27.0", "node_count": 5, "node_pools": None}
            )(),
            runtime=type(
                "RuntimeConfig",
                (),
                {"container_runtime": "docker", "cni": None, "storage_class": None, "kernel": None},
            )(),
        )
        node_detector = Mock(spec=LocalNodeDetector)
        node_detector.detect.return_value = sample_node_info
        builder = EnvironmentBuilder(
            config=config,
            node_detector=node_detector,
            fingerprint_generator=fake_fingerprint_generator,
        )
        env = builder.build()
        assert env.cluster == "override-cluster"

        assert env.kubernetes is not None
        assert env.kubernetes.version == "v1.27.0"
        assert env.kubernetes.nodeCount == 5

        assert env.runtime is not None
        assert env.runtime.containerRuntime == "docker"
