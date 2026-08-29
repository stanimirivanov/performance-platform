"""Run repository with specialized queries."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from perfeng.storage.generated_models import Environments, TestRuns
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import RunCreate, RunFilter, RunUpdate


class RunRepository(BaseRepository[TestRuns, RunCreate]):
    """Repository for TestRun operations."""

    def __init__(self):
        super().__init__(TestRuns)

    async def get_by_id(
        self,
        session: AsyncSession,
        run_id: UUID,
    ) -> TestRuns | None:
        """Get run by ID with eager loading of environment."""
        result = await session.execute(
            select(TestRuns)
            .options(selectinload(TestRuns.environments))
            .where(TestRuns.run_id == run_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        session: AsyncSession,
        run_id: UUID,
        update_data: RunUpdate,
    ) -> TestRuns | None:
        """Update a run."""

        run = await self.get_by_id(session, run_id)
        if not run:
            return None
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(run, key, value)
        await session.flush()
        return run

    async def list_with_filters(
        self,
        session: AsyncSession,
        filters: RunFilter,
    ) -> list[TestRuns]:
        """List runs with advanced filters."""

        query = select(TestRuns)
        if filters.fingerprint:
            query = query.join(TestRuns.environments)

        query = self.apply_filters(
            query,
            TestRuns.status == filters.status if filters.status else None,
            TestRuns.test_name.ilike(f"%{filters.test_name}%") if filters.test_name else None,
            TestRuns.start_time >= filters.start_date if filters.start_date else None,
            TestRuns.start_time <= filters.end_date if filters.end_date else None,
            Environments.fingerprint_hash == filters.fingerprint if filters.fingerprint else None,
        )

        query = (
            query.order_by(TestRuns.start_time.desc()).limit(filters.limit).offset(filters.offset)
        )
        result = await session.execute(query)
        return list(result.scalars().all())
