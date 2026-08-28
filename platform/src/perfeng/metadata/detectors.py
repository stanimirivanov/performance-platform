"""Functions to detect cluster, node, and runtime information."""

import json
import os
import platform
import socket
import subprocess
from typing import Any

import psutil

from perfeng.generated.environment import CpuArchitecture, NodePool


def detect_cluster_info(timeout_seconds: int = 30) -> dict[str, Any]:
    """Detect cluster name, type, and node count."""
    info = {"name": "local", "type": "docker", "node_count": 1}

    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        if result.returncode == 0:
            info["type"] = "k8s"
            context_result = subprocess.run(
                ["kubectl", "config", "current-context"],
                capture_output=True,
                text=True,
            )
            if context_result.returncode == 0:
                info["name"] = context_result.stdout.strip()

            nodes_result = subprocess.run(
                ["kubectl", "get", "nodes", "-o", "json"],
                capture_output=True,
                text=True,
            )
            if nodes_result.returncode == 0:
                nodes = json.loads(nodes_result.stdout)
                info["node_count"] = len(nodes.get("items", []))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        info["name"] = socket.gethostname()
        info["type"] = "docker"

    return info


def detect_node_info() -> dict[str, Any]:
    """Detect OS, kernel, architecture, and resources."""
    info = {
        "os": platform.system(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "resources": {},
    }
    try:
        info["resources"] = {
            "cpu_cores": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "disk_total_gb": psutil.disk_usage("/").total / (1024**3),
        }
    except Exception:
        info["resources"] = {"cpu_cores": os.cpu_count() or 1}
    return info


def detect_node_pools() -> list[NodePool] | None:
    """Detect Kubernetes node pools."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "nodes", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        nodes = json.loads(result.stdout)
        node_pools = []
        for node in nodes.get("items", []):
            status = node.get("status", {})
            capacity = status.get("capacity", {})
            labels = node.get("metadata", {}).get("labels", {})
            arch = labels.get("kubernetes.io/arch", "amd64")
            node_pool = NodePool(
                name=node.get("metadata", {}).get("name"),
                nodeModel=labels.get("node.kubernetes.io/instance-type"),
                cpuArchitecture=CpuArchitecture(arch) if arch in ("amd64", "arm64") else None,
                cpuCount=_parse_cpu_count(capacity.get("cpu")),
                memoryGiB=_parse_memory_gib(capacity.get("memory")),
            )
            node_pools.append(node_pool)
        return node_pools if node_pools else None
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return None


def _parse_cpu_count(cpu_str: str | None) -> int | None:
    if not cpu_str:
        return None
    try:
        if cpu_str.endswith("m"):
            return int(cpu_str[:-1]) // 1000
        return int(cpu_str)
    except ValueError:
        return None


def _parse_memory_gib(memory_str: str | None) -> float | None:
    if not memory_str:
        return None
    try:
        if memory_str.endswith("Ki"):
            return int(memory_str[:-2]) / (1024**2)
        elif memory_str.endswith("Mi"):
            return int(memory_str[:-2]) / 1024
        elif memory_str.endswith("Gi"):
            return int(memory_str[:-2])
        elif memory_str.endswith("Ti"):
            return int(memory_str[:-2]) * 1024
        else:
            return int(memory_str) / (1024**3)
    except ValueError:
        return None


def get_kubernetes_version() -> str | None:
    """Get Kubernetes version."""
    try:
        result = subprocess.run(
            ["kubectl", "version", "--short", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            version_info = json.loads(result.stdout)
            return version_info.get("serverVersion", {}).get("gitVersion")
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return None


def detect_container_runtime() -> str | None:
    """Detect container runtime."""
    try:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "nodes",
                "-o",
                'jsonpath="{.items[0].status.nodeInfo.containerRuntimeVersion}"',
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip().strip('"')
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def detect_cni() -> str | None:
    """Detect CNI provider."""
    cni_providers = {
        "calico": "calico",
        "flannel": "flannel",
        "weave": "weave",
        "cilium": "cilium",
        "canal": "canal",
        "antrea": "antrea",
    }
    try:
        for provider, name in cni_providers.items():
            result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "-n",
                    "kube-system",
                    "-l",
                    f"app={provider}",
                    "-o",
                    "name",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return name
    except subprocess.TimeoutExpired:
        pass
    return None


def detect_storage_class() -> str | None:
    """Detect default storage class."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "storageclass", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            storage_classes = json.loads(result.stdout)
            for sc in storage_classes.get("items", []):
                annotations = sc.get("metadata", {}).get("annotations", {})
                if annotations.get("storageclass.kubernetes.io/is-default-class") == "true":
                    return sc.get("metadata", {}).get("name")
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return None
