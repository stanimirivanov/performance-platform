# examples/usage/collect_metadata_demo.py
"""
Demonstration of how to use the metadata collector to collect
and output run metadata matching the run-metadata-example.json structure.
"""

import json
import sys
from pathlib import Path

# Add platform/src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "platform" / "src"))

from perfeng.metadata.collector import get_metadata_collector
from perfeng.metadata.config_loader import create_collector_for_environment


def collect_metadata_demo():
    """
    Demo function that collects metadata and formats it
    to match the run-metadata-example.json structure.
    """
    # Create collector
    collector = get_metadata_collector()

    # Collect environment
    env = collector.collect_environment()

    # Convert to dictionary
    env_dict = {
        "cluster": env.cluster,
        "kubernetesVersion": env.kubernetes.version if env.kubernetes else None,
        "nodeCount": env.kubernetes.nodeCount if env.kubernetes else 1,
        "kernel": env.runtime.kernel if env.runtime else None,
        "containerRuntime": env.runtime.containerRuntime if env.runtime else None,
        "cni": env.runtime.cni if env.runtime else None,
        "storageClass": env.runtime.storageClass if env.runtime else None,
        "fingerprint": env.fingerprint,
    }

    # Build full run metadata structure
    run_metadata = {
        "run": {
            "id": "perf-20240115-143022-ab12cd34",  # Would be generated
            "suite": "checkout-api",
            "profile": "regression",
            "timestamp": "2024-01-15T14:30:22Z",
            "trigger": "ci",
            "status": "COMPLETED",
            "policyVersion": "1.0.0",
            "notes": "Example run for demonstration purposes",
        },
        "test": {
            "type": "api",
            "tool": "k6",
            "toolVersion": "0.48.0",
            "scenario": "checkout-flow",
            "workloadVersion": "1.2.0",
            "configHash": "abc123def456",
        },
        "candidate": {
            "gitSha": "1234567890abcdef1234567890abcdef12345678",
            "imageDigest": "sha256:abcdef1234567890",
            "version": "2.1.0",
            "branch": "main",
            "configurationHash": "config123",
            "featureFlags": {"new-checkout": "enabled", "payment-v2": "disabled"},
            "databaseMigrationVersion": "20240115_001",
        },
        "environment": env_dict,
        "runtime": {
            "replicas": 3,
            "cpuRequests": "500m",
            "cpuLimits": "1000m",
            "memoryRequests": "512Mi",
            "memoryLimits": "1024Mi",
            "hpa": {
                "enabled": True,
                "minReplicas": 2,
                "maxReplicas": 10,
                "targetCpuUtilization": 70,
            },
        },
        "data": {
            "datasetId": "checkout-dataset",
            "datasetVersion": "2.0.0",
            "databaseSize": "10GB",
            "seedVersion": "20240101",
        },
        "phases": {
            "provisionStart": "2024-01-15T14:00:00Z",
            "warmupStart": "2024-01-15T14:10:00Z",
            "measurementStart": "2024-01-15T14:30:22Z",
            "measurementEnd": "2024-01-15T14:45:22Z",
            "cooldownEnd": "2024-01-15T14:50:00Z",
        },
    }

    return run_metadata


def demo_collect_from_environment():
    """Demo showing actual environment collection."""
    # Create collector for local environment
    collector = create_collector_for_environment("local")

    # Collect environment spec
    env = collector.collect_environment()

    print("\n=== Collected Environment Information ===")
    print(f"Cluster: {env.cluster}")
    print(f"Fingerprint: {env.fingerprint}")

    if env.kubernetes:
        print(f"Kubernetes Version: {env.kubernetes.version}")
        print(f"Node Count: {env.kubernetes.nodeCount}")

    if env.runtime:
        print(f"Container Runtime: {env.runtime.containerRuntime}")
        print(f"CNI: {env.runtime.cni}")
        print(f"Kernel: {env.runtime.kernel}")

    # Show JSON output
    print("\n=== JSON Output ===")
    env_json = json.dumps(env.model_dump(exclude_none=True), indent=2)
    print(env_json)


def demo_compare_environments():
    """Demo showing how to compare different environments."""
    local = create_collector_for_environment("local")
    dev = create_collector_for_environment("dev")

    env_local = local.collect_environment()
    env_dev = dev.collect_environment()

    print("\n=== Environment Comparison ===")
    print(f"Local fingerprint: {env_local.fingerprint[:16]}...")
    print(f"Dev fingerprint: {env_dev.fingerprint[:16]}...")

    if env_local.fingerprint != env_dev.fingerprint:
        print("✓ Environments have different fingerprints (as expected)")
    else:
        print("✗ Environments have same fingerprint (unexpected)")


if __name__ == "__main__":
    print("=== Run Metadata Example ===")
    metadata = collect_metadata_demo()
    print(json.dumps(metadata, indent=2))

    demo_collect_from_environment()
    demo_compare_environments()
