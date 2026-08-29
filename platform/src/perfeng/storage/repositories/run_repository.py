"""Run repository with specialized queries."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from perfeng.storage.generated_models import Environments, TestRuns
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import RunCreate, RunUpdate


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
        status: str | None = None,
        test_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        fingerprint: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TestRuns]:
        """List runs with advanced filters."""

        query = select(TestRuns)
        conditions = []

        if status:
            conditions.append(TestRuns.status == status)
        if test_name:
            conditions.append(TestRuns.test_name.ilike(f"%{test_name}%"))
        if start_date:
            conditions.append(TestRuns.start_time >= start_date)
        if end_date:
            conditions.append(TestRuns.start_time <= end_date)

        if fingerprint:
            query = query.join(TestRuns.environments)
            conditions.append(Environments.fingerprint_hash == fingerprint)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(TestRuns.start_time.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        return list(result.scalars().all())
