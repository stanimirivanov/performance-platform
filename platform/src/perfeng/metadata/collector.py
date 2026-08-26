"""
Metadata collection utility for automatic environment detection
and test run metadata capture.
"""

import hashlib
import json
import os
import platform
import socket
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import requests
import yaml


@dataclass
class EnvironmentInfo:
    """Environment information for fingerprinting."""

    cluster_name: str
    cluster_type: str
    kubernetes_version: str | None
    cloud_provider: str | None
    cloud_region: str | None
    cloud_zone: str | None
    node_count: int
    node_os: str
    node_kernel: str
    node_architecture: str
    node_resource_capacity: dict[str, Any]
    fingerprint_hash: str


@dataclass
class TestMetadata:
    """Complete test metadata."""

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
    environment: EnvironmentInfo


class MetadataCollector:
    """Collects environment and test metadata automatically."""

    def __init__(self, config_path: str | None = None):
        self.config = self._load_config(config_path)
        self.override_values = {}

    def _load_config(self, config_path: str | None) -> dict[str, Any]:
        """Load collector configuration."""
        default_config = {
            "auto_detect": True,
            "timeout_seconds": 30,
            "cloud_providers": ["aws", "gcp", "azure"],
            "kubeconfig_path": os.environ.get("KUBECONFIG", "~/.kube/config"),
            "fingerprint_excludes": [],
        }

        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    def set_override(self, key: str, value: Any) -> None:
        """Set manual override for a metadata value."""
        self.override_values[key] = value

    def collect_environment(self) -> EnvironmentInfo:
        """
        Collect environment information automatically.
        Supports manual overrides.
        """
        # Check for overrides first
        if "environment" in self.override_values:
            return EnvironmentInfo(**self.override_values["environment"])

        # Auto-detect environment
        cluster_info = self._detect_cluster_info()
        node_info = self._detect_node_info()
        cloud_info = self._detect_cloud_provider()
        k8s_version = self._get_kubernetes_version()

        # Generate fingerprint
        fingerprint_hash = self._generate_fingerprint(
            cluster_info.get("name", "unknown"),
            k8s_version,
            cloud_info.get("provider"),
            node_info.get("os"),
        )

        return EnvironmentInfo(
            cluster_name=cluster_info.get("name", "local-cluster"),
            cluster_type=cluster_info.get("type", "unknown"),
            kubernetes_version=k8s_version,
            cloud_provider=cloud_info.get("provider"),
            cloud_region=cloud_info.get("region"),
            cloud_zone=cloud_info.get("zone"),
            node_count=cluster_info.get("node_count", 1),
            node_os=node_info.get("os", platform.system()),
            node_kernel=node_info.get("kernel", platform.release()),
            node_architecture=node_info.get("architecture", platform.machine()),
            node_resource_capacity=node_info.get("resources", {}),
            fingerprint_hash=fingerprint_hash,
        )

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

    def _detect_cluster_info(self) -> dict[str, Any]:
        """Detect cluster information."""
        info = {"name": "local", "type": "docker", "node_count": 1}

        # Check for Kubernetes
        try:
            # Try using kubectl
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
            # Not in Kubernetes environment
            info["name"] = socket.gethostname()
            info["type"] = "docker"

        return info

    def _detect_node_info(self) -> dict[str, Any]:
        """Detect node information."""
        info = {
            "os": platform.system(),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "resources": {},
        }

        # Get CPU info
        try:
            import psutil

            info["resources"] = {
                "cpu_cores": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_total_gb": psutil.disk_usage("/").total / (1024**3),
            }
        except ImportError:
            # Fallback to basic info
            info["resources"] = {"cpu_cores": os.cpu_count() or 1}

        return info

    def _detect_cloud_provider(self) -> dict[str, str]:
        """Detect cloud provider from environment."""
        provider = None
        region = None
        zone = None

        # Check for cloud provider metadata
        try:
            # AWS
            if os.environ.get("AWS_DEFAULT_REGION"):
                provider = "aws"
                region = os.environ.get("AWS_DEFAULT_REGION")
                zone = os.environ.get("AWS_AVAILABILITY_ZONE")

            # GCP
            elif os.environ.get("CLOUDSDK_CONFIG"):
                provider = "gcp"
                # Try to get from metadata
                try:
                    response = requests.get(
                        "http://metadata.google.internal/computeMetadata/v1/instance/zone",
                        headers={"Metadata-Flavor": "Google"},
                        timeout=5,
                    )
                    if response.status_code == 200:
                        zone = response.text.strip().split("/")[-1]
                        region = "-".join(zone.split("-")[:-1])
                except:
                    pass

            # Azure
            elif os.environ.get("AZURE_RESOURCE_GROUP"):
                provider = "azure"
                region = os.environ.get("AZURE_LOCATION")
                zone = os.environ.get("AZURE_ZONE")

        except Exception:
            pass

        return {"provider": provider, "region": region, "zone": zone}

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

    def _generate_fingerprint(
        self, cluster_name: str, k8s_version: str | None, cloud_provider: str | None, node_os: str
    ) -> str:
        """Generate environment fingerprint hash."""
        # Create fingerprint string
        fingerprint_parts = [
            cluster_name or "",
            k8s_version or "",
            cloud_provider or "",
            node_os or "",
        ]

        # Filter out excluded parts
        for exclude in self.config.get("fingerprint_excludes", []):
            if exclude in fingerprint_parts:
                fingerprint_parts.remove(exclude)

        fingerprint_string = "|".join(fingerprint_parts)

        # Hash it
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()


# Utility functions
def get_metadata_collector(config_path: str | None = None) -> MetadataCollector:
    """Factory function for metadata collector."""
    return MetadataCollector(config_path)


def collect_run_metadata(test_name: str, **kwargs) -> dict[str, Any]:
    """Convenience function to collect run metadata."""
    collector = MetadataCollector()
    metadata = collector.collect_test_metadata(test_name, **kwargs)
    return asdict(metadata)


# Command-line interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collect test metadata")
    parser.add_argument("test_name", help="Name of the test")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--output", help="Output file for metadata (JSON)")
    parser.add_argument("--overrides", help="JSON string of overrides")

    args = parser.parse_args()

    collector = MetadataCollector(args.config)

    if args.overrides:
        overrides = json.loads(args.overrides)
        for key, value in overrides.items():
            collector.set_override(key, value)

    metadata = collector.collect_test_metadata(args.test_name)

    output = asdict(metadata)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2, default=str)
        print(f"Metadata written to {args.output}")
    else:
        print(json.dumps(output, indent=2, default=str))
