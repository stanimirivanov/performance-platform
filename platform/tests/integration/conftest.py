"""
Integration test fixtures.
These fixtures may set up external dependencies like test databases,
API clients, or real environment connections.
"""

import subprocess
import time
from collections.abc import Generator
from typing import Any

import pytest

from perfeng.metadata.collector import MetadataCollector
from perfeng.metadata.config_loader import create_collector_for_environment


@pytest.fixture(scope="session")
def test_postgres_container() -> Generator[dict[str, Any], None, None]:
    """
    Start a temporary PostgreSQL container for integration tests.
    Requires Docker to be installed.
    """
    import docker
    from docker.errors import NotFound

    client = docker.from_env()
    container_name = "perfeng_test_postgres"

    # Clean up any existing container with the same name
    try:
        existing = client.containers.get(container_name)
        existing.stop()
        existing.remove()
    except NotFound:
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

    # Get host port
    container.reload()
    host_port = container.ports["5432/tcp"][0]["HostPort"]

    # Wait for PostgreSQL to be ready
    max_attempts = 30
    for attempt in range(max_attempts):
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
    try:
        container.stop()
    except Exception:
        pass


@pytest.fixture
def integration_collector() -> MetadataCollector:
    """Return a collector configured for integration tests (using test config)."""
    # Use a configuration that points to a test environment
    collector = create_collector_for_environment("test")
    return collector


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
