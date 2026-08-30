"""Integration tests for SnapshotRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.repositories import RunRepository, SnapshotRepository
from perfeng.storage.schemas import RunCreate, SnapshotCreate, SnapshotFilter


@pytest.mark.asyncio
async def test_create_snapshot(db_session: AsyncSession):
    run_repo = RunRepository()
    snapshot_repo = SnapshotRepository()

    # Create a parent run
    run = await run_repo.create(db_session, RunCreate(test_name="snap-run", status="running"))

    snap_data = SnapshotCreate(
        resource_type="cpu",
        value_current=42.0,
        unit="percent",
        test_phase="steady",
    )
    snapshot = await snapshot_repo.create_for_run(db_session, run.run_id, snap_data)

    assert snapshot.snapshot_id is not None
    assert snapshot.run_id == run.run_id
    assert snapshot.resource_type == "cpu"
    assert snapshot.value_current == 42.0


@pytest.mark.asyncio
async def test_list_snapshots_by_resource_type(db_session: AsyncSession):
    run_repo = RunRepository()
    snapshot_repo = SnapshotRepository()

    run = await run_repo.create(db_session, RunCreate(test_name="list-snap", status="running"))

    # Create two snapshots with different resource types
    await snapshot_repo.create_for_run(
        db_session,
        run.run_id,
        SnapshotCreate(resource_type="cpu", value_current=10.0),
    )
    await snapshot_repo.create_for_run(
        db_session,
        run.run_id,
        SnapshotCreate(resource_type="memory", value_current=20.0),
    )

    # Filter by resource_type=cpu
    filters = SnapshotFilter(resource_type="cpu", limit=10, offset=0)
    snaps = await snapshot_repo.list_by_run(db_session, run.run_id, filters)
    assert len(snaps) == 1
    assert snaps[0].resource_type == "cpu"
