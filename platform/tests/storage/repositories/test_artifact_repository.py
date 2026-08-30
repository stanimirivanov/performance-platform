"""Integration tests for ArtifactRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.repositories import ArtifactRepository, RunRepository
from perfeng.storage.schemas import ArtifactCreate, ArtifactFilter, RunCreate


@pytest.mark.asyncio
async def test_create_artifact(db_session: AsyncSession):
    run_repo = RunRepository()
    artifact_repo = ArtifactRepository()

    run = await run_repo.create(db_session, RunCreate(test_name="artifact-run", status="completed"))

    artifact_data = ArtifactCreate(
        artifact_type="raw_data",
        data_type="current",
        storage_path="path/to/file.json",
        checksum="abc123",
    )
    artifact = await artifact_repo.create_for_run(db_session, run.run_id, artifact_data)

    assert artifact.artifact_id is not None
    assert artifact.run_id == run.run_id
    assert artifact.artifact_type == "raw_data"
    assert artifact.data_type == "current"


@pytest.mark.asyncio
async def test_list_artifacts_by_data_type(db_session: AsyncSession):
    run_repo = RunRepository()
    artifact_repo = ArtifactRepository()

    run = await run_repo.create(
        db_session, RunCreate(test_name="list-artifacts", status="completed")
    )

    await artifact_repo.create_for_run(
        db_session,
        run.run_id,
        ArtifactCreate(artifact_type="raw", data_type="baseline", storage_path="b.json"),
    )
    await artifact_repo.create_for_run(
        db_session,
        run.run_id,
        ArtifactCreate(artifact_type="processed", data_type="comparison", storage_path="c.json"),
    )

    filters = ArtifactFilter(data_type="baseline", limit=10, offset=0)
    artifacts = await artifact_repo.list_by_run(db_session, run.run_id, filters)
    assert len(artifacts) == 1
    assert artifacts[0].data_type == "baseline"
