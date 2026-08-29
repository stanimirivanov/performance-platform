"""Run service with business logic."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from injector import inject
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.database import get_session
from perfeng.storage.repositories.environment_repository import EnvironmentRepository
from perfeng.storage.repositories.run_repository import RunRepository
from perfeng.storage.schemas import (
    EnvironmentCreate,
    EnvironmentResponse,
    RunCreate,
    RunCreateResponse,
    RunResponse,
    RunUpdate,
)


class RunService:
    """Service for run operations."""

    @inject
    def __init__(self, run_repo: RunRepository, env_repo: EnvironmentRepository):
        self.run_repo = run_repo
        self.env_repo = env_repo

    async def create_run(
        self,
        session: AsyncSession,
        run_data: RunCreate,
        environment_data: EnvironmentCreate | None = None,
    ) -> RunCreateResponse:
        """Create a new run with optional environment."""

        run = await self.run_repo.create(session, run_data)
        response = RunCreateResponse(run_id=run.run_id)
        if environment_data:
            env = await self.env_repo.create_for_run(session, run.run_id, environment_data)
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
        status: str | None = None,
        test_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        fingerprint: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RunResponse]:
        """List runs with filters, returning Pydantic models."""

        runs = await self.run_repo.list_with_filters(
            session, status, test_name, start_date, end_date, fingerprint, limit, offset
        )
        return [RunResponse.model_validate(run) for run in runs]
