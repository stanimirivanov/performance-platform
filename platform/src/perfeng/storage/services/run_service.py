"""Run service with business logic."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.database import get_session
from perfeng.storage.repositories import EnvironmentRepository, RunRepository
from perfeng.storage.schemas import (
    EnvironmentResponse,
    RunCreate,
    RunCreateResponse,
    RunFilter,
    RunResponse,
    RunUpdate,
)


class RunService:
    """Service for run operations."""

    def __init__(self, run_repo: RunRepository, env_repo: EnvironmentRepository):
        self.run_repo = run_repo
        self.env_repo = env_repo

    async def create_run(
        self,
        session: AsyncSession,
        run_data: RunCreate,
    ) -> RunCreateResponse:
        """Create a new run with optional embedded environment."""

        run = await self.run_repo.create(session, run_data)
        response = RunCreateResponse(run_id=run.run_id)
        if run_data.environment:
            env = await self.env_repo.create_for_run(session, run.run_id, run_data.environment)
            response.environment_id = env.environment_id
        return response

    async def get_run(
        self,
        session: AsyncSession,
        run_id: UUID,
    ) -> RunResponse | None:
        """Get a run with its environment."""

        run = await self.run_repo.get_by_id(session, run_id)
        if not run:
            return None
        run_response = RunResponse.model_validate(run)
        if run.environments:
            run_response.environment = EnvironmentResponse.model_validate(run.environments)
        return run_response

    async def update_run(
        self,
        session: AsyncSession,
        run_id: UUID,
        update_data: RunUpdate,
    ) -> RunResponse | None:
        """Update a run and return the updated object."""

        updated_run = await self.run_repo.update(session, run_id, update_data)
        if not updated_run:
            return None
        return RunResponse.model_validate(updated_run)

    async def list_runs(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        filters: RunFilter,
    ) -> list[RunResponse]:
        """List runs with filters, returning Pydantic models."""

        runs = await self.run_repo.list_with_filters(session, filters)
        return [RunResponse.model_validate(run) for run in runs]
