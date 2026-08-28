"""Dependency injection for API routes."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..storage import EnvironmentRepository, RunRepository, RunService, get_session


async def get_run_service(
    session: AsyncSession = Depends(get_session),
) -> RunService:
    """Dependency for RunService."""
    run_repo = RunRepository(session)
    env_repo = EnvironmentRepository(session)
    return RunService(run_repo, env_repo)
