"""Dependency injection for API routes (composition root)."""

from injector import Module, provider, singleton

from perfeng.storage.repositories.artifact_repository import ArtifactRepository
from perfeng.storage.repositories.environment_repository import EnvironmentRepository
from perfeng.storage.repositories.event_repository import EventRepository
from perfeng.storage.repositories.run_repository import RunRepository
from perfeng.storage.repositories.snapshot_repository import SnapshotRepository
from perfeng.storage.services.artifact_service import ArtifactService
from perfeng.storage.services.event_service import EventService
from perfeng.storage.services.run_service import RunService
from perfeng.storage.services.snapshot_service import SnapshotService


class AppModule(Module):
    """Registers all application components as singletons.

    Repositories are stateless (they hold no persistent state; they receive
    an AsyncSession per method call), so singletons are safe.
    """

    @provider
    @singleton
    def provide_run_repository(self) -> RunRepository:
        # Repository instances do NOT hold a session; session is passed
        # to methods by the service layer.
        return RunRepository.__new__(
            RunRepository
        )  # we will not use constructor injection for session

    @provider
    @singleton
    def provide_environment_repository(self) -> EnvironmentRepository:
        return EnvironmentRepository.__new__(EnvironmentRepository)

    @provider
    @singleton
    def provide_snapshot_repository(self) -> SnapshotRepository:
        return SnapshotRepository.__new__(SnapshotRepository)

    @provider
    @singleton
    def provide_event_repository(self) -> EventRepository:
        return EventRepository.__new__(EventRepository)

    @provider
    @singleton
    def provide_artifact_repository(self) -> ArtifactRepository:
        return ArtifactRepository.__new__(ArtifactRepository)

    @provider
    @singleton
    def provide_run_service(
        self,
        run_repo: RunRepository,
        env_repo: EnvironmentRepository,
    ) -> RunService:
        return RunService(run_repo, env_repo)

    @provider
    @singleton
    def provide_snapshot_service(self, snapshot_repo: SnapshotRepository) -> SnapshotService:
        return SnapshotService(snapshot_repo)

    @provider
    @singleton
    def provide_event_service(self, event_repo: EventRepository) -> EventService:
        return EventService(event_repo)

    @provider
    @singleton
    def provide_artifact_service(self, artifact_repo: ArtifactRepository) -> ArtifactService:
        return ArtifactService(artifact_repo)
