"""Dependency providers for API services (stateless singletons)."""

from perfeng.storage.repositories import (
    ArtifactRepository,
    EnvironmentRepository,
    EventRepository,
    RunRepository,
    SnapshotRepository,
)
from perfeng.storage.services import ArtifactService, EventService, RunService, SnapshotService

# ---------------------------------------------------------------------------
# Instantiate services once (they are stateless; repositories don't hold
# sessions, so this is safe).
# ---------------------------------------------------------------------------

run_service = RunService(
    run_repo=RunRepository(),
    env_repo=EnvironmentRepository(),
)

snapshot_service = SnapshotService(snapshot_repo=SnapshotRepository())

event_service = EventService(event_repo=EventRepository())

artifact_service = ArtifactService(artifact_repo=ArtifactRepository())


# ---------------------------------------------------------------------------
# Dependency functions
# ---------------------------------------------------------------------------


async def get_run_service() -> RunService:
    return run_service


async def get_snapshot_service() -> SnapshotService:
    return snapshot_service


async def get_event_service() -> EventService:
    return event_service


async def get_artifact_service() -> ArtifactService:
    return artifact_service
