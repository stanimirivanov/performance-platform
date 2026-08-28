"""Environment repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perfeng.storage.models import Environment
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import EnvironmentCreate


class EnvironmentRepository(BaseRepository[Environment, EnvironmentCreate]):
    """Repository for Environment operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Environment, session)

    async def create_for_run(self, run_id: UUID, env_data: EnvironmentCreate) -> Environment:
        """Create an environment for a specific run."""
        env = Environment(run_id=run_id, **env_data.model_dump())
        self.session.add(env)
        await self.session.flush()
        return env

    async def get_by_fingerprint(self, fingerprint_hash: str) -> list[Environment]:
        """Find environments by fingerprint."""
        result = await self.session.execute(
            select(Environment).where(Environment.fingerprint_hash == fingerprint_hash)
        )
        return list(result.scalars().all())

    async def get_by_run(self, run_id: UUID) -> Environment | None:
        """Get environment for a specific run."""
        result = await self.session.execute(select(Environment).where(Environment.run_id == run_id))
        return result.scalar_one_or_none()
