"""
Tests for legacy builder wrappers (build_environment_spec, build_performance_run_metadata).
"""

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.metadata.builders.legacy import build_environment_spec, build_performance_run_metadata


def test_build_environment_spec_from_dict():
    raw_config = {
        "auto_detect": False,
        "timeout_seconds": 30,
        "environment_config": {
            "cluster": "test-cluster",
            "kubernetes": {"version": "v1.28.0", "nodeCount": 3},
            "runtime": {
                "containerRuntime": "containerd",
                "cni": "calico",
                "storageClass": "standard",
                "kernel": "5.15.0",
            },
        },
    }
    env = build_environment_spec(raw_config)
    assert isinstance(env, EnvironmentSpecification)
    assert env.cluster == "test-cluster"

    assert env.kubernetes is not None
    assert env.kubernetes.version == "v1.28.0"

    assert env.runtime is not None
    assert env.runtime.containerRuntime == "containerd"


def test_build_performance_run_metadata_from_kwargs():
    env = EnvironmentSpecification(
        cluster="test",
        fingerprint="a" * 64,
        kubernetes=None,
        runtime=None,
        application=None,
        compatibility=None,
    )
    kwargs = {
        "test_profile": "smoke",
        "trigger_type": "ci",
        "tool": "k6",
        "toolVersion": "0.45.0",
        "scenario": "flow",
        "gitSha": "a" * 40,
        "version": "1.0.0",
        "branch": "main",
        "configurationHash": "hash",
        "featureFlags": {"debug": True},
    }
    metadata = build_performance_run_metadata("test-suite", "running", env, kwargs)
    assert isinstance(metadata, PerformanceRunMetadata)
    assert metadata.run.suite == "test-suite"
    assert metadata.test.tool.value == "k6"
    assert metadata.candidate.gitSha == "a" * 40
