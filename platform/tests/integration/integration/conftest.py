"""
Integration test fixtures.
These fixtures may set up external dependencies like test databases,
API clients, or real environment connections.
"""

import contextlib
import subprocess
import time
from collections.abc import Generator
from typing import Any

import docker
import pytest

from perfeng.metadata.collector import MetadataCollector, get_metadata_collector


@pytest.fixture(scope="session")
def test_postgres_container() -> Generator[dict[str, Any], None, None]:
    """
    Start a temporary PostgreSQL container for integration tests.
    Requires Docker and the 'docker' Python package.
    """

    try:
        client = docker.from_env()  # type: ignore
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")

    container_name = "perfeng_test_postgres"

    # Clean up any existing container with the same name
    try:
        existing = client.containers.get(container_name)
        existing.stop()
        existing.remove()
    except docker.errors.NotFound:  # type: ignore
        pass

    # Run PostgreSQL container
    container = client.containers.run(
        image="postgres:15-alpine",
        name=container_name,
        environment={
            "POSTGRES_DB": "test_metadata",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_password",
        },
        ports={"5432/tcp": None},  # Random port
        detach=True,
        remove=True,
    )

    # Get host port safely
    container.reload()
    port_mapping = container.ports.get("5432/tcp")
    if not port_mapping:
        # Cleanup and skip
        container.stop()
        pytest.skip("Could not get port mapping for PostgreSQL container")

    # port_mapping is a list of dicts with HostPort
    host_port = port_mapping[0]["HostPort"]

    # Wait for PostgreSQL to be ready
    max_attempts = 30
    for _attempt in range(max_attempts):
        try:
            subprocess.run(
                [
                    "pg_isready",
                    "-h",
                    "localhost",
                    "-p",
                    host_port,
                    "-U",
                    "test_user",
                    "-d",
                    "test_metadata",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            break
        except subprocess.CalledProcessError:
            time.sleep(1)
    else:
        raise RuntimeError("PostgreSQL container did not start in time")

    # Provide connection details
    connection_info = {
        "host": "localhost",
        "port": host_port,
        "database": "test_metadata",
        "user": "test_user",
        "password": "test_password",
        "dsn": f"postgresql://test_user:test_password@localhost:{host_port}/test_metadata",
    }

    yield connection_info

    # Cleanup
    with contextlib.suppress(Exception):
        container.stop()


@pytest.fixture
def integration_collector() -> MetadataCollector:
    """Return a collector configured for integration tests (using test config)."""
    return get_metadata_collector("test")


@pytest.fixture
def mock_k8s_api() -> Generator[None, None, None]:
    """
    Mock the Kubernetes API for integration tests that need to simulate
    a real cluster without actually connecting.
    """
    # This can be implemented using a fake Kubernetes client or by patching
    # the subprocess calls to return predefined responses.
    # For now, we'll just yield a placeholder.
    # In a real implementation, you might use the 'k8s' library with a test server.
    yield None
