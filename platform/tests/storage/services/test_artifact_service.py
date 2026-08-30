"""Unit tests for ArtifactService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.models import DataArtifacts
from perfeng.storage.repositories.artifact_repository import ArtifactRepository
from perfeng.storage.schemas import ArtifactCreate, ArtifactFilter, ArtifactResponse
from perfeng.storage.services.artifact_service import ArtifactService


@pytest.fixture
def mock_artifact_repo():
    return Mock(spec=ArtifactRepository)


@pytest.fixture
def service(mock_artifact_repo):
    return ArtifactService(mock_artifact_repo)


def make_fake_artifact(**kwargs):
    defaults = {
        "artifact_id": uuid4(),
        "run_id": uuid4(),
        "artifact_type": "raw",
        "data_type": "current",
        "created_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return DataArtifacts(**defaults)


@pytest.mark.asyncio
async def test_create_artifact(service, mock_artifact_repo):
    session = AsyncMock(spec=AsyncSession)
    run_id = uuid4()
    data = ArtifactCreate(artifact_type="raw", data_type="current", storage_path="x.json")
    fake_artifact = make_fake_artifact(run_id=run_id)
    mock_artifact_repo.create_for_run = AsyncMock(return_value=fake_artifact)

    result = await service.create_artifact(session, run_id, data)

    mock_artifact_repo.create_for_run.assert_awaited_once_with(session, run_id, data)
    assert isinstance(result, ArtifactResponse)
    assert result.artifact_id == fake_artifact.artifact_id


@pytest.mark.asyncio
async def test_list_artifacts(service, mock_artifact_repo):
    session = AsyncMock(spec=AsyncSession)
    run_id = uuid4()
    filters = ArtifactFilter(data_type="baseline", limit=10, offset=0)
    fake_artifacts = [make_fake_artifact()]
    mock_artifact_repo.list_by_run = AsyncMock(return_value=fake_artifacts)

    result = await service.list_artifacts(session, run_id, filters)

    mock_artifact_repo.list_by_run.assert_awaited_once_with(session, run_id, filters)
    assert len(result) == 1
    assert isinstance(result[0], ArtifactResponse)
