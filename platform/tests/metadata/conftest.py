"""
Fixtures for metadata package tests.
"""

from __future__ import annotations

import json
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest

from perfeng.metadata.collector import MetadataCollector
from perfeng.metadata.config import CollectorConfig
from perfeng.metadata.detectors import LocalNodeDetector


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
def collector_config_no_detect() -> CollectorConfig:
    """Typed config with auto-detection disabled."""
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
def fake_local_detector() -> Generator[LocalNodeDetector, None, None]:
    """LocalNodeDetector with mocked psutil to return predictable values."""
    detector = LocalNodeDetector()
    with patch("perfeng.metadata.detectors.local.psutil") as mock_psutil:
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.virtual_memory.return_value.total = 16 * (1024**3)
        mock_psutil.disk_usage.return_value.total = 100 * (1024**3)
        yield detector
    # Note: This fixture yields inside patch context; careful with yield.
    # Better to use a factory that returns a detector with mocked methods.
    # We'll adjust: use a fixture that patches LocalNodeDetector.detect directly.


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
