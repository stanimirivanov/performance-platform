"""Additional tests for MetadataPersistenceClient."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from perfeng.integration.persistence import MetadataPersistenceClient


@pytest.mark.asyncio
async def test_context_manager_close_with_injected_client():
    mock_client = AsyncMock()
    client = MetadataPersistenceClient(base_url="http://test", client=mock_client)
    async with client as c:
        assert c is client
    # The injected client must not be closed by the facade
    mock_client.aclose.assert_not_awaited()
    mock_client.close.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_without_injected_client_calls_repository():
    with patch("perfeng.integration.persistence.StorageRunRepository") as repo_cls:
        repo = Mock()
        repo.close = AsyncMock()
        repo_cls.return_value = repo

        client = MetadataPersistenceClient(base_url="http://test")
        await client.close()

        repo.close.assert_awaited_once()
