"""Additional tests for MetadataPersistenceClient."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from perfeng.integration.persistence import MetadataPersistenceClient


@pytest.mark.asyncio
async def test_context_manager_close():
    mock_client = AsyncMock()
    # AsyncMock has both close and aclose; our close prefers aclose
    client = MetadataPersistenceClient(base_url="http://test", client=mock_client)
    async with client as c:
        assert c is client
    mock_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_without_client():
    # When no client injected, internal repository has resilient http client; we can't easily mock.
    # Just ensure no exception is raised and that underlying client is closed.
    # We'll patch StorageRunRepository to avoid actual HTTP.
    with patch("perfeng.integration.persistence.StorageRunRepository") as repo_cls:
        repo = Mock()
        repo.close = AsyncMock()
        repo_cls.return_value = repo
        client = MetadataPersistenceClient(base_url="http://test")
        await client.close()
        repo.close.assert_awaited_once()
