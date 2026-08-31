# examples/collect_metadata.py
"""
Demonstration of how to use the metadata collector to collect
and output run metadata matching the run-metadata-example.json structure.
"""

import json

from perfeng.metadata.collector import MetadataInput, get_metadata_collector


def collect_metadata_demo():
    """
    Demo function that collects metadata and formats it
    to match the run-metadata-example.json structure.
    """
    # Create collector (defaults to local environment, auto_detect=True)
    collector = get_metadata_collector()

    # Define test metadata with desired parameters
    test_meta = MetadataInput(
        test_profile="regression",
        trigger_type="ci",
        tool="k6",
        tool_version="0.48.0",
        test_type="api",
        scenario="checkout-flow",
        git_sha="1234567890abcdef1234567890abcdef12345678",
        version="2.1.0",
        branch="main",
        configuration_hash="config123",
        feature_flags={"new-checkout": "enabled", "payment-v2": "disabled"},
        database_migration_version="20240115_001",
        replicas=3,
        cpu_requests="500m",
        cpu_limits="1000m",
        memory_requests="512Mi",
        memory_limits="1024Mi",
        hpa={"enabled": True, "min_replicas": 2, "max_replicas": 10, "target_cpu_utilization": 70},
        dataset_id="checkout-dataset",
        dataset_version="2.0.0",
        database_size="10GB",
        seed_version="20240101",
        policy_version="1.0.0",
        notes="Example run for demonstration purposes",
    )

    # Collect full run metadata (includes environment, candidate, etc.)
    run_metadata_model = collector.collect_test_metadata(
        test_name="checkout-api",
        status="COMPLETED",
        test_metadata=test_meta,
    )

    # Convert to dictionary with all fields
    return run_metadata_model.model_dump(exclude_none=True)


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
    env_json = json.dumps(env.model_dump(exclude_none=True), indent=2)
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
