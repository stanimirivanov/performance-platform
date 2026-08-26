"""
Main conftest file that imports global fixtures and adds any additional
shared fixtures for all test groups.
"""

# Import all global fixtures so they are available to all tests
from pathlib import Path

import pytest

from tests.conftest_global import *  # noqa: F401, F403


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def sample_data_dir() -> Path:
    """Return path to sample data directory."""
    return Path(__file__).parent / "data"
