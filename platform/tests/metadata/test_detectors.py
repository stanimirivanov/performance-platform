"""
Tests for detectors: parsers, local node detector, kubernetes detector, kubectl client.
"""

from unittest.mock import Mock, patch

import psutil
import pytest

from perfeng.generated.environment import CpuArchitecture
from perfeng.metadata.detectors import (
    ClusterInfo,
    ClusterType,
    KubectlClient,
    KubectlError,
    KubernetesClusterDetector,
    LocalNodeDetector,
    ResourceParser,
)


class TestResourceParser:
    def test_cpu_count_plain(self):
        assert ResourceParser.cpu_count("4") == 4

    def test_cpu_count_millicores(self):
        assert ResourceParser.cpu_count("1500m") == 1  # truncated

    def test_cpu_count_invalid(self):
        assert ResourceParser.cpu_count("abc") is None
        assert ResourceParser.cpu_count(None) is None

    def test_memory_gib(self):
        assert ResourceParser.memory_gib("16Gi") == 16.0
        assert ResourceParser.memory_gib("512Mi") == 0.5
        assert ResourceParser.memory_gib("1.5Gi") == 1.5
        assert ResourceParser.memory_gib("1024Ki") == 1.0 / 1024
        assert ResourceParser.memory_gib("invalid") is None
        assert ResourceParser.memory_gib(None) is None


class TestLocalNodeDetector:
    @patch("perfeng.metadata.detectors.local.psutil")
    @patch("perfeng.metadata.detectors.local.platform")
    def test_detect(self, mock_platform, mock_psutil):
        mock_platform.system.return_value = "Linux"
        mock_platform.release.return_value = "5.15.0"
        mock_platform.machine.return_value = "x86_64"
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.virtual_memory.return_value.total = 16 * (1024**3)
        mock_psutil.disk_usage.return_value.total = 100 * (1024**3)

        detector = LocalNodeDetector()
        node = detector.detect()

        assert node.os == "Linux"
        assert node.kernel == "5.15.0"
        assert node.architecture == "x86_64"
        assert node.resources.cpu_cores == 8
        assert node.resources.memory_total_gb == 16.0
        assert node.resources.disk_total_gb == 100.0

        def test_detect_psutil_failure(self):
            detector = LocalNodeDetector()
            with (
                patch(
                    "perfeng.metadata.detectors.local.psutil.cpu_count",
                    side_effect=psutil.Error,
                ),
                patch("perfeng.metadata.detectors.local.os.cpu_count", return_value=4),
            ):
                node = detector.detect()
                assert node.resources.cpu_cores == 4  # fallback to os.cpu_count


class TestKubectlClient:
    def test_run_success(self):
        client = KubectlClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")
            result = client.run("get", "nodes")
            assert result == "output"

    def test_run_file_not_found(self):
        client = KubectlClient()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(KubectlError):
                client.run("get", "nodes")

    def test_run_nonzero_exit(self):
        client = KubectlClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="error")
            with pytest.raises(KubectlError):
                client.run("get", "nodes")

    def test_fetch_json_caching(self):
        client = KubectlClient()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='{"items": []}', stderr="")
            result1 = client.get_nodes()
            result2 = client.get_nodes()
            assert mock_run.call_count == 1  # cached
            assert result1 == {"items": []}
            assert result2 == {"items": []}


class TestKubernetesClusterDetector:
    def test_detect_k8s(self):
        client = Mock(spec=KubectlClient)
        client.run.return_value = ""
        client.current_context.return_value = "test-context"
        client.get_nodes.return_value = {"items": [{"metadata": {}}, {"metadata": {}}]}

        detector = KubernetesClusterDetector(client=client)
        info = detector.detect()

        assert info == ClusterInfo(
            name="test-context",
            type=ClusterType.KUBERNETES,
            node_count=2,
        )

    def test_detect_fallback_docker(self):
        client = Mock(spec=KubectlClient)
        client.run.side_effect = KubectlError("kubectl missing")

        detector = KubernetesClusterDetector(client=client)
        info = detector.detect()

        assert info.type == ClusterType.DOCKER
        assert info.node_count == 1

    def test_detect_version(self):
        client = Mock(spec=KubectlClient)
        client.version.return_value = {"serverVersion": {"gitVersion": "v1.28.0"}}
        detector = KubernetesClusterDetector(client=client)
        assert detector.detect_version() == "v1.28.0"

    def test_detect_node_pools(self):
        nodes = {
            "items": [
                {
                    "metadata": {
                        "name": "node1",
                        "labels": {
                            "kubernetes.io/arch": "amd64",
                            "node.kubernetes.io/instance-type": "m5.xlarge",
                        },
                    },
                    "status": {
                        "capacity": {
                            "cpu": "4",
                            "memory": "16Gi",
                        }
                    },
                }
            ]
        }
        client = Mock(spec=KubectlClient)
        client.get_nodes.return_value = nodes
        detector = KubernetesClusterDetector(client=client)
        pools = detector.detect_node_pools()

        assert pools is not None
        assert len(pools) == 1
        pool = pools[0]
        assert pool.name == "node1"
        assert pool.cpuArchitecture == CpuArchitecture.amd64
        assert pool.cpuCount == 4
        assert pool.memoryGiB == 16.0

    def test_detect_container_runtime(self):
        client = Mock(spec=KubectlClient)
        client.run.return_value = '"containerd://1.6.0"'
        detector = KubernetesClusterDetector(client=client)
        assert detector.detect_container_runtime() == "containerd://1.6.0"

    def test_detect_cni(self):
        client = Mock(spec=KubectlClient)
        client.get_pods.return_value = "pod/calico-node-abc"
        detector = KubernetesClusterDetector(client=client)
        assert detector.detect_cni() == "calico"

    def test_detect_storage_class(self):
        storage = {
            "items": [
                {
                    "metadata": {
                        "name": "standard",
                        "annotations": {"storageclass.kubernetes.io/is-default-class": "true"},
                    }
                }
            ]
        }
        client = Mock(spec=KubectlClient)
        client.get_storage_classes.return_value = storage
        detector = KubernetesClusterDetector(client=client)
        assert detector.detect_storage_class() == "standard"
