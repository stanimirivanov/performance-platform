"""Run service with business logic."""

from datetime import datetime
from typing import Any
from uuid import UUID

from ..repositories.environment_repository import EnvironmentRepository
from ..repositories.run_repository import RunRepository
from ..schemas import EnvironmentCreate, RunCreate, RunUpdate


class RunService:
    """Service for run operations."""

    def __init__(self, run_repo: RunRepository, env_repo: EnvironmentRepository):
        self.run_repo = run_repo
        self.env_repo = env_repo

    async def create_run(
        self,
        run_data: RunCreate,
        environment_data: EnvironmentCreate | None = None,
    ) -> dict[str, Any]:
        """Create a new run with optional environment."""
        run = await self.run_repo.create(run_data)
        result = {"run_id": run.run_id}
        if environment_data:
            env = await self.env_repo.create_for_run(run.run_id, environment_data)
            result["environment_id"] = env.environment_id
        return result

    async def get_run(self, run_id: UUID) -> dict[str, Any] | None:
        """Get a run with environment."""
        run = await self.run_repo.get_by_id(run_id)
        if not run:
            return None
        env = await self.env_repo.get_by_run(run_id)
        return {"run": run, "environment": env}

    async def update_run(self, run_id: UUID, update_data: RunUpdate) -> TestRun | None:
        """Update a run."""
        return await self.run_repo.update(run_id, update_data)

    async def list_runs(
        self,
        status: str | None = None,
        test_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        fingerprint: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TestRun]:
        """List runs with filters."""
        return await self.run_repo.list_with_filters(
            status, test_name, start_date, end_date, fingerprint, limit, offset
        )
