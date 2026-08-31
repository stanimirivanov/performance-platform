"""Kubernetes cluster and node-pool detection."""

from __future__ import annotations

import socket
from typing import Any

from perfeng.generated.environment import CpuArchitecture, NodePool
from perfeng.metadata.detectors.kubernetes_client import KubectlClient, KubectlError
from perfeng.metadata.detectors.parsers import ResourceParser
from perfeng.metadata.detectors.types import ClusterInfo, ClusterType


class KubernetesClusterDetector:
    """Detect Kubernetes cluster topology, version, and configuration."""

    _CNI_LABELS: dict[str, str] = {
        "calico": "app=calico",
        "flannel": "app=flannel",
        "weave": "app=weave",
        "cilium": "app=cilium",
        "canal": "app=canal",
        "antrea": "app=antrea",
    }

    def __init__(self, client: KubectlClient | None = None, timeout: int = 10) -> None:
        self._client = client or KubectlClient(timeout=timeout)

    def detect(self) -> ClusterInfo:
        """Detect cluster info, falling back to local/docker when kubectl is unavailable."""
        try:
            return self._detect_k8s()
        except KubectlError:
            return ClusterInfo(
                name=socket.gethostname(),
                type=ClusterType.DOCKER,
                node_count=1,
            )

    def _detect_k8s(self) -> ClusterInfo:
        # Smoke-test that the cluster is reachable
        self._client.run("cluster-info")

        try:
            name = self._client.current_context()
        except KubectlError:
            name = "unknown"

        nodes = self._client.get_nodes()
        node_count = len(nodes.get("items", []))

        return ClusterInfo(
            name=name,
            type=ClusterType.KUBERNETES,
            node_count=node_count,
        )

    def detect_node_pools(self) -> list[NodePool] | None:
        """Build NodePool objects from the live Kubernetes node list."""
        try:
            nodes = self._client.get_nodes()
        except KubectlError:
            return None

        pools = [self._parse_node(n) for n in nodes.get("items", [])]
        return pools or None

    def _parse_node(self, node: dict[str, Any]) -> NodePool:
        metadata = node.get("metadata", {})
        status = node.get("status", {})
        capacity = status.get("capacity", {})
        labels = metadata.get("labels", {})

        arch_label = labels.get("kubernetes.io/arch", "amd64")

        return NodePool(
            name=metadata.get("name"),
            nodeModel=labels.get("node.kubernetes.io/instance-type"),
            cpuArchitecture=self._resolve_architecture(arch_label),
            cpuCount=ResourceParser.cpu_count(capacity.get("cpu")),
            memoryGiB=ResourceParser.memory_gib(capacity.get("memory")),
        )

    @staticmethod
    def _resolve_architecture(arch: str) -> CpuArchitecture | None:
        try:
            return CpuArchitecture(arch)
        except ValueError:
            return None

    def detect_version(self) -> str | None:
        """Return the Kubernetes server version (gitVersion)."""
        try:
            version_info = self._client.version()
            return version_info.get("serverVersion", {}).get("gitVersion")
        except KubectlError:
            return None

    def detect_container_runtime(self) -> str | None:
        """Return the container runtime version of the first node."""
        try:
            output = self._client.run(
                "get",
                "nodes",
                "-o",
                'jsonpath="{.items[0].status.nodeInfo.containerRuntimeVersion}"',
            )
            return output.strip().strip('"')
        except KubectlError:
            return None

    def detect_cni(self) -> str | None:
        """Detect the CNI provider by looking for known pods in kube-system."""
        try:
            for name, label in self._CNI_LABELS.items():
                output = self._client.get_pods("kube-system", label)
                if output.strip():
                    return name
        except KubectlError:
            pass
        return None

    def detect_storage_class(self) -> str | None:
        """Return the name of the default StorageClass, if any."""
        try:
            storage_classes = self._client.get_storage_classes()
            for sc in storage_classes.get("items", []):
                annotations = sc.get("metadata", {}).get("annotations", {})
                if annotations.get("storageclass.kubernetes.io/is-default-class") == "true":
                    return sc.get("metadata", {}).get("name")
        except KubectlError:
            pass
        return None
