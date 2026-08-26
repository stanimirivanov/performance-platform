# platform/tests/metadata/conftest.py
"""
Metadata-specific fixtures.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from perfeng.metadata.collector import MetadataCollector


@pytest.fixture
def temp_config_file() -> Path:
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config = {
            "auto_detect": False,
            "timeout_seconds": 30,
            "fingerprint_excludes": [],
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
        yaml.dump(config, f)
        config_path = Path(f.name)

    yield config_path

    # Cleanup
    if config_path.exists():
        config_path.unlink()


@pytest.fixture
def mock_subprocess() -> Mock:
    """Mock subprocess.run for testing."""
    with patch("subprocess.run") as mock_run:
        # Default successful responses
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(
                {"items": [{"metadata": {"name": "node1"}}, {"metadata": {"name": "node2"}}]}
            ),
            stderr="",
        )
        yield mock_run


@pytest.fixture
def collector() -> MetadataCollector:
    """Create a basic collector instance."""
    return MetadataCollector()


@pytest.fixture
def collector_with_config(temp_config_file) -> MetadataCollector:
    """Create a collector with configuration."""
    return MetadataCollector(temp_config_file)


@pytest.fixture
def sample_environment_dict() -> dict:
    """Sample environment data for testing."""
    return {
        "cluster": "test-cluster",
        "fingerprint": "a" * 64,
        "kubernetes": {"version": "v1.28.0", "nodeCount": 3, "nodePools": []},
        "runtime": {
            "containerRuntime": "containerd",
            "cni": "calico",
            "storageClass": "standard",
            "kernel": "5.15.0",
        },
        "application": {
            "configurationHash": "config123",
            "featureFlags": {"debug": True, "trace": False},
        },
    }


@pytest.fixture
def sample_test_metadata() -> dict:
    """Sample test metadata for testing."""
    return {
        "test_name": "load-test",
        "test_script": "load_test.py",
        "test_profile": "medium-load",
        "status": "running",
        "thresholds": {"p95": 100, "p99": 200},
        "parameters": {"users": 100, "duration": 60},
        "tags": ["performance", "load"],
        "triggered_by": "jenkins",
        "trigger_type": "ci",
        "ci_build_id": "build-123",
        "ci_job_id": "job-456",
    }


@pytest.fixture
def mock_kubectl_available() -> Mock:
    """Mock kubectl as available."""
    with patch("subprocess.run") as mock_run:

        def side_effect(*args, **kwargs):
            if "cluster-info" in str(args):
                return Mock(returncode=0, stdout="", stderr="")
            elif "current-context" in str(args):
                return Mock(returncode=0, stdout="test-context\n", stderr="")
            elif "get nodes" in str(args):
                return Mock(
                    returncode=0,
                    stdout=json.dumps(
                        {
                            "items": [
                                {"metadata": {"name": "node1"}},
                                {"metadata": {"name": "node2"}},
                                {"metadata": {"name": "node3"}},
                            ]
                        }
                    ),
                    stderr="",
                )
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect
        yield mock_run


@pytest.fixture
def mock_kubectl_not_available() -> Mock:
    """Mock kubectl as not available."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("kubectl not found")
        yield mock_run
