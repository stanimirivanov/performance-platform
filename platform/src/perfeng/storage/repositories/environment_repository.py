"""Environment repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.models import Environments
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import EnvironmentCreate


class EnvironmentRepository(BaseRepository[Environments, EnvironmentCreate]):
    """Repository for Environment operations."""

    def __init__(self):
        super().__init__(Environments)

    async def create_for_run(
        self,
        session: AsyncSession,
        run_id: UUID,
        env_data: EnvironmentCreate,
    ) -> Environments:
        """Create an environment for a specific run."""

        env = Environments(run_id=run_id, **env_data.model_dump())
        session.add(env)
        await session.flush()
        return env

    async def get_by_fingerprint(
        self,
        session: AsyncSession,
        fingerprint_hash: str,
    ) -> list[Environments]:
        """Find environments by fingerprint."""

        result = await session.execute(
            select(Environments).where(Environments.fingerprint_hash == fingerprint_hash)
        )
        return list(result.scalars().all())

    async def get_by_run(
        self,
        session: AsyncSession,
        run_id: UUID,
    ) -> Environments | None:
        """Get environment for a specific run."""

        result = await session.execute(select(Environments).where(Environments.run_id == run_id))
        return result.scalar_one_or_none()
