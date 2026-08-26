"""
Metadata collection utility using the Environment Specification schema.
Collects metadata about the test runner environment and creates
properly structured EnvironmentSpecification objects.
"""

import hashlib
import json
import os
import platform
import socket
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
import yaml

from perfeng.generated.environment import (
    Application,
    CpuArchitecture,
    EnvironmentSpecification,
    Kubernetes,
    NodePool,
    Runtime,
)


@dataclass
class TestMetadata:
    """Complete test metadata with environment specification."""

    test_name: str
    test_script: str | None
    test_profile: str | None
    status: str
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int | None
    thresholds: dict[str, Any]
    parameters: dict[str, Any]
    tags: list[str]
    triggered_by: str
    trigger_type: str
    ci_build_id: str | None
    ci_job_id: str | None
    environment: EnvironmentSpecification


class MetadataCollector:
    """
    Collects metadata about the test runner environment using the
    Environment Specification schema.

    The collector detects the environment where the test runner is executing
    and creates a validated EnvironmentSpecification object.
    """

    def __init__(self, config_path: str | Path | None = None):
        self.config = self._load_config(config_path)
        self.override_values = {}
        self._environment_cache: EnvironmentSpecification | None = None

    def _load_config(self, config_path: str | Path | None) -> dict[str, Any]:
        """Load collector configuration."""
        default_config = {
            "auto_detect": True,
            "timeout_seconds": 30,
            "kubeconfig_path": os.environ.get("KUBECONFIG", "~/.kube/config"),
            "fingerprint_excludes": [],
            "environment_config": {
                "cluster": os.environ.get("PERFENG_CLUSTER_NAME", "local"),
                "kubernetes": {
                    "version": os.environ.get("PERFENG_K8S_VERSION"),
                    "nodeCount": int(os.environ.get("PERFENG_NODE_COUNT", 1)),
                },
                "runtime": {
                    "containerRuntime": os.environ.get("PERFENG_CONTAINER_RUNTIME"),
                    "cni": os.environ.get("PERFENG_CNI"),
                    "storageClass": os.environ.get("PERFENG_STORAGE_CLASS"),
                    "kernel": os.environ.get("PERFENG_KERNEL_VERSION"),
                },
            },
        }

        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    # Deep merge
                    default_config = self._deep_merge(default_config, user_config)

        return default_config

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def set_override(self, key: str, value: Any) -> None:
        """Set manual override for a metadata value."""
        self.override_values[key] = value

    def collect_environment(self) -> EnvironmentSpecification:
        """
        Collect environment information and return as validated schema.

        Priority:
        1. Manual overrides
        2. Environment variables (PERFENG_*)
        3. Configuration file
        4. Auto-detection (if enabled)
        """
        # Check for overrides first
        if "environment" in self.override_values:
            env_data = self.override_values["environment"]
            return EnvironmentSpecification(**env_data)

        # Check cache
        if self._environment_cache:
            return self._environment_cache

        # Build environment spec
        if self.config.get("auto_detect", True):
            env_spec = self._collect_environment_auto()
        else:
            env_spec = self._collect_environment_from_config()

        # Cache and return
        self._environment_cache = env_spec
        return env_spec

    def _collect_environment_auto(self) -> EnvironmentSpecification:
        """Auto-detect environment with config fallbacks."""
        env_config = self.config.get("environment_config", {})

        # Detect cluster info
        cluster_info = self._detect_cluster_info()
        node_info = self._detect_node_info()
        k8s_version = self._get_kubernetes_version()

        # Build Kubernetes object
        kubernetes = Kubernetes(
            version=k8s_version or env_config.get("kubernetes", {}).get("version"),
            node_count=cluster_info.get("node_count", 1),
            node_pools=self._detect_node_pools(),
        )

        # Build Runtime object
        runtime = Runtime(
            container_runtime=self._detect_container_runtime(),
            cni=self._detect_cni(),
            storage_class=self._detect_storage_class(),
            kernel=node_info.get("kernel", platform.release()),
        )

        # Build Application object (if configured)
        application = None
        if env_config.get("application"):
            application = Application(
                configuration_hash=env_config.get("application", {}).get("configurationHash"),
                feature_flags=env_config.get("application", {}).get("featureFlags", {}),
            )

        # Get cluster name
        cluster_name = env_config.get("cluster") or cluster_info.get("name", "local")

        # Generate fingerprint
        fingerprint = self._generate_fingerprint(
            cluster_name=cluster_name,
            k8s_version=kubernetes.version,
            node_os=node_info.get("os", ""),
            container_runtime=runtime.container_runtime,
        )

        # Create specification
        env_spec = EnvironmentSpecification(
            cluster=cluster_name,
            fingerprint=fingerprint,
            kubernetes=kubernetes,
            runtime=runtime,
            application=application,
            compatibility=None,  # Will be evaluated separately
        )

        return env_spec

    def _collect_environment_from_config(self) -> EnvironmentSpecification:
        """Collect environment purely from configuration."""
        env_config = self.config.get("environment_config", {})
        node_info = self._detect_node_info()

        kubernetes = Kubernetes(
            version=env_config.get("kubernetes", {}).get("version"),
            node_count=env_config.get("kubernetes", {}).get("nodeCount", 1),
            node_pools=env_config.get("kubernetes", {}).get("nodePools"),
        )

        runtime = Runtime(
            container_runtime=env_config.get("runtime", {}).get("containerRuntime"),
            cni=env_config.get("runtime", {}).get("cni"),
            storage_class=env_config.get("runtime", {}).get("storageClass"),
            kernel=node_info.get("kernel", platform.release()),
        )

        application = None
        if env_config.get("application"):
            application = Application(
                configuration_hash=env_config.get("application", {}).get("configurationHash"),
                feature_flags=env_config.get("application", {}).get("featureFlags", {}),
            )

        fingerprint = self._generate_fingerprint(
            cluster_name=env_config.get("cluster", "configured-cluster"),
            k8s_version=kubernetes.version,
            node_os=node_info.get("os", platform.system()),
            container_runtime=runtime.container_runtime,
        )

        return EnvironmentSpecification(
            cluster=env_config.get("cluster", "configured-cluster"),
            fingerprint=fingerprint,
            kubernetes=kubernetes,
            runtime=runtime,
            application=application,
            compatibility=None,
        )

    def _detect_cluster_info(self) -> dict[str, Any]:
        """Detect cluster information from the test runner environment."""
        info = {"name": "local", "type": "docker", "node_count": 1}

        # Check for Kubernetes
        try:
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=self.config["timeout_seconds"],
            )
            if result.returncode == 0:
                info["type"] = "k8s"
                # Get cluster name from context
                context_result = subprocess.run(
                    ["kubectl", "config", "current-context"], capture_output=True, text=True
                )
                if context_result.returncode == 0:
                    info["name"] = context_result.stdout.strip()

                # Get node count
                nodes_result = subprocess.run(
                    ["kubectl", "get", "nodes", "-o", "json"], capture_output=True, text=True
                )
                if nodes_result.returncode == 0:
                    nodes = json.loads(nodes_result.stdout)
                    info["node_count"] = len(nodes.get("items", []))

        except (subprocess.TimeoutExpired, FileNotFoundError):
            info["name"] = socket.gethostname()
            info["type"] = "docker"

        return info

    def _detect_node_info(self) -> dict[str, Any]:
        """Detect node information from the test runner."""
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

    def _detect_node_pools(self) -> list[NodePool] | None:
        """Detect Kubernetes node pools if available."""
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
                # Parse node info
                status = node.get("status", {})
                capacity = status.get("capacity", {})

                # Get architecture from labels
                labels = node.get("metadata", {}).get("labels", {})
                arch = labels.get("kubernetes.io/arch", "amd64")

                node_pool = NodePool(
                    name=node.get("metadata", {}).get("name"),
                    node_model=labels.get("node.kubernetes.io/instance-type"),
                    cpu_architecture=CpuArchitecture(arch) if arch in ["amd64", "arm64"] else None,
                    cpu_count=self._parse_cpu_count(capacity.get("cpu")),
                    memory_gi_b=self._parse_memory_gib(capacity.get("memory")),
                )
                node_pools.append(node_pool)

            return node_pools if node_pools else None

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return None

    def _parse_cpu_count(self, cpu_str: str) -> int | None:
        """Parse CPU count from Kubernetes capacity string."""
        if not cpu_str:
            return None
        try:
            if cpu_str.endswith("m"):
                return int(cpu_str[:-1]) // 1000
            return int(cpu_str)
        except ValueError:
            return None

    def _parse_memory_gib(self, memory_str: str) -> float | None:
        """Parse memory from Kubernetes capacity string to GiB."""
        if not memory_str:
            return None
        try:
            # Parse Ki, Mi, Gi, Ti
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

    def _get_kubernetes_version(self) -> str | None:
        """Get Kubernetes version if available."""
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

    def _detect_container_runtime(self) -> str | None:
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

    def _detect_cni(self) -> str | None:
        """Detect CNI provider."""
        # Check for common CNI providers
        cni_providers = {
            "calico": "calico",
            "flannel": "flannel",
            "weave": "weave",
            "cilium": "cilium",
            "canal": "canal",
            "antrea": "antrea",
        }

        try:
            for provider in cni_providers:
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
                    return cni_providers[provider]
        except subprocess.TimeoutExpired:
            pass
        return None

    def _detect_storage_class(self) -> str | None:
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

    def _generate_fingerprint(
        self,
        cluster_name: str,
        k8s_version: str | None,
        node_os: str,
        container_runtime: str | None,
    ) -> str:
        """Generate environment fingerprint hash following the schema pattern."""
        fingerprint_parts = [
            cluster_name or "",
            k8s_version or "",
            node_os or "",
            container_runtime or "",
        ]

        # Apply exclusions
        excludes = self.config.get("fingerprint_excludes", [])
        fingerprint_parts = [p for p in fingerprint_parts if p not in excludes]

        fingerprint_string = "|".join(fingerprint_parts)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    def collect_test_metadata(
        self, test_name: str, status: str = "pending", **kwargs
    ) -> TestMetadata:
        """
        Collect complete test metadata.

        Args:
            test_name: Name of the test
            status: Initial status
            **kwargs: Additional test parameters
        """
        # Get environment
        environment = self.collect_environment()

        # Build test metadata
        metadata = TestMetadata(
            test_name=test_name,
            test_script=kwargs.get("test_script"),
            test_profile=kwargs.get("test_profile"),
            status=status,
            start_time=datetime.utcnow(),
            end_time=None,
            duration_seconds=None,
            thresholds=kwargs.get("thresholds", {}),
            parameters=kwargs.get("parameters", {}),
            tags=kwargs.get("tags", []),
            triggered_by=kwargs.get("triggered_by", os.environ.get("USER", "unknown")),
            trigger_type=kwargs.get("trigger_type", "manual"),
            ci_build_id=kwargs.get("ci_build_id", os.environ.get("CI_BUILD_ID")),
            ci_job_id=kwargs.get("ci_job_id", os.environ.get("CI_JOB_ID")),
            environment=environment,
        )

        # Apply overrides
        if "test_metadata" in self.override_values:
            override = self.override_values["test_metadata"]
            for key, value in override.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)

        return metadata


# Utility functions
def get_metadata_collector(config_path: str | Path | None = None) -> MetadataCollector:
    """Factory function for metadata collector."""
    return MetadataCollector(config_path)


def collect_run_metadata(test_name: str, **kwargs) -> dict[str, Any]:
    """Convenience function to collect run metadata."""
    collector = MetadataCollector()
    metadata = collector.collect_test_metadata(test_name, **kwargs)
    return asdict(metadata)
