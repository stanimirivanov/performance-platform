"""Dependency injection for API routes (composition root)."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.database import get_session
from perfeng.storage.repositories.artifact_repository import ArtifactRepository
from perfeng.storage.repositories.environment_repository import EnvironmentRepository
from perfeng.storage.repositories.event_repository import EventRepository
from perfeng.storage.repositories.run_repository import RunRepository
from perfeng.storage.repositories.snapshot_repository import SnapshotRepository
from perfeng.storage.services.artifact_service import ArtifactService
from perfeng.storage.services.event_service import EventService
from perfeng.storage.services.run_service import RunService
from perfeng.storage.services.snapshot_service import SnapshotService


async def get_run_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RunService:
    """Build RunService with concrete repositories."""
    run_repo = RunRepository(session)
    env_repo = EnvironmentRepository(session)
    return RunService(run_repo, env_repo)


RunServiceDep = Annotated[RunService, Depends(get_run_service)]


async def get_snapshot_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SnapshotService:
    repo = SnapshotRepository(session)
    return SnapshotService(repo)


SnapshotServiceDep = Annotated[SnapshotService, Depends(get_snapshot_service)]


async def get_event_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EventService:
    repo = EventRepository(session)
    return EventService(repo)


EventServiceDep = Annotated[EventService, Depends(get_event_service)]


async def get_artifact_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ArtifactService:
    repo = ArtifactRepository(session)
    return ArtifactService(repo)


ArtifactServiceDep = Annotated[ArtifactService, Depends(get_artifact_service)]
