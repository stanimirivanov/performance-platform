# examples/collect_metadata.py
"""
Demonstration of how to use the metadata collector to collect
and output run metadata matching the run-metadata-example.json structure.
"""

import json
from datetime import datetime

from perfeng.metadata.builders.config import (
    CandidateConfig,
    DataConfig,
    EnvironmentOverrideConfig,
    ExecutorConfig,
    PhasesConfig,
    RunConfig,
    RunMetadataBuildConfig,
    RunRuntimeConfig,
)
from perfeng.metadata.collector import get_metadata_collector


def parse_dt(iso_str: str) -> datetime:
    """Parse an ISO 8601 string (with optional Z) to an aware datetime."""
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))


def collect_metadata_demo():
    """
    Demo function that collects metadata and outputs a structured dictionary.
    """
    # Build the full run metadata configuration directly
    run_metadata_config = RunMetadataBuildConfig(
        test_name="checkout-api",
        status="COMPLETED",
        run=RunConfig(
            profile="regression",
            trigger="ci",
            policy_version="1.0.0",
            notes="Example run for demonstration purposes",
        ),
        test=ExecutorConfig(
            tool="k6",
            tool_version="0.48.0",
            test_type="api",
            scenario="checkout-flow",
            workload_version="1.2.0",
            config_hash="abc123def456",
        ),
        candidate=CandidateConfig(
            git_sha="1234567890abcdef1234567890abcdef12345678",
            image_digest="sha256:abcdef1234567890",
            version="2.1.0",
            branch="main",
            configuration_hash="config123",
            feature_flags={"new-checkout": "enabled", "payment-v2": "disabled"},
            database_migration_version="20240115_001",
        ),
        runtime=RunRuntimeConfig(
            replicas=3,
            cpu_requests="500m",
            cpu_limits="1000m",
            memory_requests="512Mi",
            memory_limits="1024Mi",
            hpa={
                "enabled": True,
                "minReplicas": 2,
                "maxReplicas": 10,
                "targetCpuUtilization": 70,
            },
        ),
        data=DataConfig(
            dataset_id="checkout-dataset",
            dataset_version="2.0.0",
            database_size="10GB",
            seed_version="20240101",
        ),
        phases=PhasesConfig(
            provision_start=parse_dt("2024-01-15T14:00:00Z"),
            warmup_start=parse_dt("2024-01-15T14:10:00Z"),
            measurement_start=parse_dt("2024-01-15T14:30:22Z"),
            measurement_end=parse_dt("2024-01-15T14:45:22Z"),
            cooldown_end=parse_dt("2024-01-15T14:50:00Z"),
        ),
        environment=EnvironmentOverrideConfig(
            node_pool="pool-1",
            node_model="m5.xlarge",
            cpu_architecture="amd64",
            region="us-west-2",
        ),
    )

    collector = get_metadata_collector()
    metadata_model = collector.collect_test_metadata(run_metadata_config)

    # Convert to JSON-safe dict (enums, datetimes, etc.)
    return metadata_model.model_dump(mode="json", exclude_none=True)


def demo_collect_from_environment():
    """Demo showing actual environment collection."""
    # Create collector for local environment
    collector = get_metadata_collector("local")

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
    env_json = json.dumps(env.model_dump(mode="json", exclude_none=True), indent=2)
    print(env_json)


def demo_compare_environments():
    """Demo showing how to compare different environments."""
    local_collector = get_metadata_collector("local")
    dev_collector = get_metadata_collector("dev")

    env_local = local_collector.collect_environment()
    env_dev = dev_collector.collect_environment()

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
