"""
Global fixtures shared across all test groups.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def examples_dir() -> Path:
    """Path to examples directory."""
    return Path(__file__).parent.parent.parent / "examples"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
