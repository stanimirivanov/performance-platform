"""Unit tests for MetadataPersistenceClient."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import Response

from perfeng.generated.run_metadata import (
    Candidate,
    Environment,
    PerformanceRunMetadata,
    Profile,
    Run,
    Status,
    Test,
    Tool,
    Trigger,
    Type,
)
from perfeng.integration.persistence import MetadataPersistenceClient


def parse_dt(iso_str: str) -> datetime:
    """Parse an ISO 8601 string (with optional Z) to an aware datetime."""
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))


def make_metadata():
    return PerformanceRunMetadata(
        run=Run(
            id="perf-20240101-000000-abcdef12",
            suite="checkout-api",
            profile=Profile.regression,
            timestamp=parse_dt("2024-01-01T00:00:00Z"),
            trigger=Trigger.ci,
            status=Status.RUNNING,
            policyVersion="1.0.0",
            notes="test run",
        ),
        test=Test(
            type=Type.api,
            tool=Tool.k6,
            toolVersion="0.45.0",
            scenario="checkout-flow.js",
            workloadVersion="1.2.3",
            configHash="abc123",
        ),
        candidate=Candidate(
            gitSha="a" * 40,
            imageDigest="sha256:abc",
            version="1.0.0",
            branch="main",
            configurationHash="cfg123",
            featureFlags={"feature_a": True},
            databaseMigrationVersion="20240101000000",
        ),
        environment=Environment(
            cluster="perf-k8s-01",
            kubernetesVersion="v1.28.0",
            nodePool="worker-perf",
            nodeModel="m5.xlarge",
            cpuArchitecture="amd64",
            kernel="5.10.0",
            containerRuntime="containerd",
            cni="calico",
            storageClass="ssd",
            fingerprint="f" * 64,
            nodeCount=3,
            region="us-west-2",
        ),
        runtime=None,
        data=None,
        phases=None,
    )


@pytest.mark.asyncio
async def test_save_posts_correct_payload():
    mock_client = AsyncMock()
    expected_response = {"run_id": str(uuid4())}
    mock_client.post.return_value = Response(
        status_code=201,
        json=expected_response,
        request=MagicMock(),
    )

    base_url = "http://testserver"
    client = MetadataPersistenceClient(base_url=base_url, client=mock_client)
    metadata = make_metadata()

    result = await client.save(metadata)

    # Verify POST URL
    mock_client.post.assert_awaited_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == f"{base_url}/api/v1/runs/"

    # Check payload structure
    payload = call_args[1]["json"]
    assert payload["test_name"] == "checkout-api"
    assert payload["status"] == "running"  # lowercased
    assert payload["test_profile"] == "regression"
    assert payload["parameters"]["tool"] == "k6"
    assert payload["environment"]["fingerprint_hash"] == "f" * 64

    # Ensure environment is embedded and not None
    assert "environment" in payload
    assert payload["environment"]["cluster_name"] == "perf-k8s-01"

    assert result == expected_response


@pytest.mark.asyncio
async def test_close_calls_aclose():
    mock_client = AsyncMock()
    client = MetadataPersistenceClient(base_url="http://test", client=mock_client)
    await client.close()
    mock_client.aclose.assert_awaited_once()
