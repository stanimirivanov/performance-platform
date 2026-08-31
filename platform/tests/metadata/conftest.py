"""
Metadata-specific fixtures.
"""

import json
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest

from perfeng.metadata.collector import MetadataCollector
from perfeng.metadata.config import CollectorConfig


@pytest.fixture
def collector_config() -> CollectorConfig:
    """Create a typed CollectorConfig for testing (no auto-detect)."""
    return CollectorConfig(
        auto_detect=False,
        timeout_seconds=30,
        fingerprint_excludes=(),
        cluster=None,
        kubernetes=None,
        runtime=None,
        application=None,
    )


@pytest.fixture
def collector(collector_config: CollectorConfig) -> MetadataCollector:
    """Create a basic collector instance with config."""
    return MetadataCollector(config=collector_config)


@pytest.fixture
def mock_subprocess() -> Generator[Mock, None, None]:
    """Mock subprocess.run for testing."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(
                {"items": [{"metadata": {"name": "node1"}}, {"metadata": {"name": "node2"}}]}
            ),
            stderr="",
        )
        yield mock_run


@pytest.fixture
def mock_kubectl_available() -> Generator[Mock, None, None]:
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
def mock_kubectl_not_available() -> Generator[Mock, None, None]:
    """Mock kubectl as not available."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("kubectl not found")
        yield mock_run
