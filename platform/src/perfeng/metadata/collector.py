# platform/src/perfeng/metadata/collector.py
"""
Metadata collection utility using the Environment Specification schema.
Collects metadata about the test runner environment and creates
properly structured EnvironmentSpecification and PerformanceRunMetadata objects.
"""

import hashlib
import json
import os
import platform
import socket
import subprocess
import uuid
from datetime import UTC, datetime
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
from perfeng.generated.run_metadata import (
    Candidate,
    Data,
    PerformanceRunMetadata,
    Phases,
    Profile,
    Run,
    Test,
    Trigger,
)
from perfeng.generated.run_metadata import Environment as RunEnvironment
from perfeng.generated.run_metadata import Runtime as RunRuntime
from perfeng.generated.run_metadata import Status as RunStatus
from perfeng.generated.run_metadata import Tool as TestTool
from perfeng.generated.run_metadata import Type as TestType


class MetadataCollector:
    """
    Collects metadata about the test runner environment using the
    Environment Specification schema.

    The collector detects the environment where the test runner is executing
    and creates a validated EnvironmentSpecification object.
    """

    def __init__(self, config_path: str | Path | None = None):
        self.config = self._load_config(config_path)
        self.override_values: dict[str, Any] = {}
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

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    def collect_environment(self) -> EnvironmentSpecification:
        """
        Collect environment information and return as validated schema.

        Priority:
        1. Manual overrides
        2. Environment variables (PERFENG_*)
        3. Configuration file
        4. Auto-detection (if enabled)
        """
        if "environment" in self.override_values:
            env_data = self.override_values["environment"]
            return EnvironmentSpecification(**env_data)

        if self._environment_cache:
            return self._environment_cache

        if self.config.get("auto_detect", True):
            env_spec = self._collect_environment_auto()
        else:
            env_spec = self._collect_environment_from_config()

        self._environment_cache = env_spec
        return env_spec

    def collect_test_metadata(
        self,
        test_name: str,
        status: str = "CREATED",
        **kwargs,
    ) -> PerformanceRunMetadata:
        """
        Collect complete test metadata and return a PerformanceRunMetadata instance.

        Args:
            test_name: Name of the test (used as suite and scenario)
            status: Initial status string (mapped to RunStatus enum)
            **kwargs: Additional parameters to populate nested models.
                Common keys: test_profile, trigger_type, tool, toolVersion,
                scenario, gitSha, version, branch, replicas, cpuRequests, etc.
        """
        # 1. Collect environment
        env_spec = self.collect_environment()
        env = self._convert_environment(env_spec, kwargs)

        # 2. Generate run ID
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        suffix = uuid.uuid4().hex[:8]
        run_id = f"perf-{ts}-{suffix}"

        # 3. Map status to enum
        status_map = {
            "created": RunStatus.CREATED,
            "validating": RunStatus.VALIDATING,
            "provisioning": RunStatus.PROVISIONING,
            "warming_up": RunStatus.WARMING_UP,
            "running": RunStatus.RUNNING,
            "collecting": RunStatus.COLLECTING,
            "analyzing": RunStatus.ANALYZING,
            "reporting": RunStatus.REPORTING,
            "completed": RunStatus.COMPLETED,
            "invalid": RunStatus.INVALID,
            "aborted": RunStatus.ABORTED,
            "infrastructure_failure": RunStatus.INFRASTRUCTURE_FAILURE,
            "test_failure": RunStatus.TEST_FAILURE,
            "inconclusive": RunStatus.INCONCLUSIVE,
        }
        run_status = status_map.get(status.lower(), RunStatus.CREATED)

        # 4. Map profile
        profile_map = {
            "smoke": Profile.smoke,
            "average": Profile.average,
            "regression": Profile.regression,
            "stress": Profile.stress,
            "capacity": Profile.capacity,
            "soak": Profile.soak,
        }
        profile_key = kwargs.get("test_profile", "regression")
        run_profile = profile_map.get(profile_key.lower(), Profile.regression)

        # 5. Map trigger
        trigger_map = {
            "manual": Trigger.manual,
            "ci": Trigger.ci,
            "schedule": Trigger.schedule,
            "bisect": Trigger.bisect,
            "release": Trigger.release,
        }
        trigger_key = kwargs.get("trigger_type", "manual")
        run_trigger = trigger_map.get(trigger_key.lower(), Trigger.manual)

        # 6. Build Run
        run = Run(
            id=run_id,
            suite=test_name,
            profile=run_profile,
            timestamp=datetime.utcnow().replace(tzinfo=UTC),
            trigger=run_trigger,
            status=run_status,
            policyVersion=kwargs.get("policyVersion"),
            notes=kwargs.get("notes"),
        )

        # 7. Build Test
        tool_map = {
            "k6": TestTool.k6,
            "playwright": TestTool.playwright,
            "kube-burner": TestTool.kube_burner,
            "benchmark-operator": TestTool.benchmark_operator,
        }
        tool = kwargs.get("tool", "k6")
        test_tool = tool_map.get(tool.lower(), TestTool.k6)

        type_map = {
            "api": TestType.api,
            "browser": TestType.browser,
            "kubernetes": TestType.kubernetes,
            "infrastructure": TestType.infrastructure,
        }
        test_type_str = kwargs.get("test_type", "api")
        test_type = type_map.get(test_type_str.lower(), TestType.api)

        test = Test(
            type=test_type,
            tool=test_tool,
            toolVersion=kwargs.get("toolVersion", "unknown"),
            scenario=kwargs.get("scenario", test_name),
            workloadVersion=kwargs.get("workloadVersion"),
            configHash=kwargs.get("configHash"),
        )

        # 8. Build Candidate
        candidate = Candidate(
            gitSha=kwargs.get("gitSha", "0" * 40),
            imageDigest=kwargs.get("imageDigest"),
            version=kwargs.get("version"),
            branch=kwargs.get("branch"),
            configurationHash=kwargs.get("configurationHash"),
            featureFlags=kwargs.get("featureFlags"),
            databaseMigrationVersion=kwargs.get("databaseMigrationVersion"),
        )

        # 9. Build optional Runtime
        runtime = None
        if any(
            key in kwargs
            for key in [
                "replicas",
                "cpuRequests",
                "cpuLimits",
                "memoryRequests",
                "memoryLimits",
                "hpa",
            ]
        ):
            runtime = RunRuntime(
                replicas=kwargs.get("replicas"),
                cpuRequests=kwargs.get("cpuRequests"),
                cpuLimits=kwargs.get("cpuLimits"),
                memoryRequests=kwargs.get("memoryRequests"),
                memoryLimits=kwargs.get("memoryLimits"),
                hpa=kwargs.get("hpa"),
            )

        # 10. Build optional Data
        data = None
        if any(
            key in kwargs
            for key in [
                "datasetId",
                "datasetVersion",
                "databaseSize",
                "seedVersion",
            ]
        ):
            data = Data(
                datasetId=kwargs.get("datasetId"),
                datasetVersion=kwargs.get("datasetVersion"),
                databaseSize=kwargs.get("databaseSize"),
                seedVersion=kwargs.get("seedVersion"),
            )

        # 11. Build optional Phases
        phases = None
        if any(
            key in kwargs
            for key in [
                "provisionStart",
                "warmupStart",
                "measurementStart",
                "measurementEnd",
                "cooldownEnd",
            ]
        ):
            phases = Phases(
                provisionStart=kwargs.get("provisionStart"),
                warmupStart=kwargs.get("warmupStart"),
                measurementStart=kwargs.get("measurementStart"),
                measurementEnd=kwargs.get("measurementEnd"),
                cooldownEnd=kwargs.get("cooldownEnd"),
            )

        # 12. Build final metadata
        metadata = PerformanceRunMetadata(
            run=run,
            test=test,
            candidate=candidate,
            environment=env,
            runtime=runtime,
            data=data,
            phases=phases,
        )

        # 13. Apply overrides (simple flat override for top-level fields)
        if "test_metadata" in self.override_values:
            override = self.override_values["test_metadata"]
            # We only support a limited set of overrides at the top level.
            # For advanced usage, users should build the metadata themselves.
            for key, value in override.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)

        return metadata

    # -------------------------------------------------------------------------
    # Environment collection helpers
    # -------------------------------------------------------------------------

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
            nodeCount=cluster_info.get("node_count", 1),
            nodePools=self._detect_node_pools(),
        )

        # Build Runtime object
        runtime = Runtime(
            containerRuntime=self._detect_container_runtime(),
            cni=self._detect_cni(),
            storageClass=self._detect_storage_class(),
            kernel=node_info.get("kernel", platform.release()),
        )

        # Build Application object (if configured)
        application = None
        if env_config.get("application"):
            application = Application(
                configurationHash=env_config.get("application", {}).get("configurationHash"),
                featureFlags=env_config.get("application", {}).get("featureFlags", {}),
            )

        # Get cluster name
        cluster_name = env_config.get("cluster") or cluster_info.get("name", "local")

        # Generate fingerprint
        fingerprint = self._generate_fingerprint(
            cluster_name=cluster_name,
            k8s_version=kubernetes.version,
            node_os=node_info.get("os", ""),
            container_runtime=runtime.containerRuntime,
        )

        return EnvironmentSpecification(
            cluster=cluster_name,
            fingerprint=fingerprint,
            kubernetes=kubernetes,
            runtime=runtime,
            application=application,
            compatibility=None,
        )

    def _collect_environment_from_config(self) -> EnvironmentSpecification:
        """Collect environment purely from configuration."""
        env_config = self.config.get("environment_config", {})
        node_info = self._detect_node_info()

        kubernetes = Kubernetes(
            version=env_config.get("kubernetes", {}).get("version"),
            nodeCount=env_config.get("kubernetes", {}).get("nodeCount", 1),
            nodePools=env_config.get("kubernetes", {}).get("nodePools"),
        )

        runtime = Runtime(
            containerRuntime=env_config.get("runtime", {}).get("containerRuntime"),
            cni=env_config.get("runtime", {}).get("cni"),
            storageClass=env_config.get("runtime", {}).get("storageClass"),
            kernel=node_info.get("kernel", platform.release()),
        )

        application = None
        if env_config.get("application"):
            application = Application(
                configurationHash=env_config.get("application", {}).get("configurationHash"),
                featureFlags=env_config.get("application", {}).get("featureFlags", {}),
            )

        fingerprint = self._generate_fingerprint(
            cluster_name=env_config.get("cluster", "configured-cluster"),
            k8s_version=kubernetes.version,
            node_os=node_info.get("os", platform.system()),
            container_runtime=runtime.containerRuntime,
        )

        return EnvironmentSpecification(
            cluster=env_config.get("cluster", "configured-cluster"),
            fingerprint=fingerprint,
            kubernetes=kubernetes,
            runtime=runtime,
            application=application,
            compatibility=None,
        )

    def _convert_environment(
        self, env_spec: EnvironmentSpecification, kwargs: dict
    ) -> RunEnvironment:
        """Convert EnvironmentSpecification to the run-metadata Environment model."""
        kubernetes = env_spec.kubernetes
        runtime = env_spec.runtime

        # Extract node pool info if available
        node_pool = None
        cpu_arch = None
        if kubernetes and kubernetes.nodePools and len(kubernetes.nodePools) > 0:
            first_pool = kubernetes.nodePools[0]
            node_pool = first_pool.name
            cpu_arch = first_pool.cpuArchitecture.value if first_pool.cpuArchitecture else None

        return RunEnvironment(
            cluster=env_spec.cluster,
            kubernetesVersion=kubernetes.version if kubernetes else "unknown",
            nodePool=kwargs.get("nodePool", node_pool),
            nodeModel=kwargs.get("nodeModel"),
            cpuArchitecture=kwargs.get("cpuArchitecture", cpu_arch),
            kernel=runtime.kernel if runtime else None,
            containerRuntime=runtime.containerRuntime if runtime else None,
            cni=runtime.cni if runtime else None,
            storageClass=runtime.storageClass if runtime else None,
            fingerprint=env_spec.fingerprint,
            nodeCount=kubernetes.nodeCount if kubernetes else None,
            region=kwargs.get("region"),
        )

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

        excludes = self.config.get("fingerprint_excludes", [])
        fingerprint_parts = [p for p in fingerprint_parts if p not in excludes]

        fingerprint_string = "|".join(fingerprint_parts)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    # -------------------------------------------------------------------------
    # Detection helpers (with error handling)
    # -------------------------------------------------------------------------

    def _detect_cluster_info(self) -> dict[str, Any]:
        """Detect cluster information from the test runner environment."""
        info = {"name": "local", "type": "docker", "node_count": 1}

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
                    ["kubectl", "config", "current-context"],
                    capture_output=True,
                    text=True,
                )
                if context_result.returncode == 0:
                    info["name"] = context_result.stdout.strip()

                # Get node count
                nodes_result = subprocess.run(
                    ["kubectl", "get", "nodes", "-o", "json"],
                    capture_output=True,
                    text=True,
                )
                if nodes_result.returncode == 0:
                    nodes = json.loads(nodes_result.stdout)
                    info["node_count"] = len(nodes.get("items", []))

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Not in Kubernetes environment
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
                status = node.get("status", {})
                capacity = status.get("capacity", {})
                labels = node.get("metadata", {}).get("labels", {})
                arch = labels.get("kubernetes.io/arch", "amd64")

                node_pool = NodePool(
                    name=node.get("metadata", {}).get("name"),
                    nodeModel=labels.get("node.kubernetes.io/instance-type"),
                    cpuArchitecture=CpuArchitecture(arch) if arch in ["amd64", "arm64"] else None,
                    cpuCount=self._parse_cpu_count(capacity.get("cpu")),
                    memoryGiB=self._parse_memory_gib(capacity.get("memory")),
                )
                node_pools.append(node_pool)

            return node_pools if node_pools else None

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return None

    def _parse_cpu_count(self, cpu_str: str | None) -> int | None:
        """Parse CPU count from Kubernetes capacity string."""
        if not cpu_str:
            return None
        try:
            if cpu_str.endswith("m"):
                return int(cpu_str[:-1]) // 1000
            return int(cpu_str)
        except ValueError:
            return None

    def _parse_memory_gib(self, memory_str: str | None) -> float | None:
        """Parse memory from Kubernetes capacity string to GiB."""
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


# -----------------------------------------------------------------------------
# Convenience functions
# -----------------------------------------------------------------------------


def get_metadata_collector(
    config_path: str | Path | None = None,
) -> MetadataCollector:
    """Factory function for metadata collector."""
    return MetadataCollector(config_path)


def collect_run_metadata(test_name: str, **kwargs) -> dict[str, Any]:
    """
    Convenience function to collect run metadata and return as a dict.
    """
    collector = MetadataCollector()
    metadata = collector.collect_test_metadata(test_name, **kwargs)
    return metadata.model_dump(exclude_none=True)
