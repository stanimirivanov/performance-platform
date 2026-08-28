"""Run repository with specialized queries."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from perfeng.storage.models import Environment, TestRun
from perfeng.storage.repositories.base import BaseRepository
from perfeng.storage.schemas import RunCreate, RunUpdate


class RunRepository(BaseRepository[TestRun, RunCreate]):
    """Repository for TestRun operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(TestRun, session)

    async def get_by_id(self, run_id: UUID) -> TestRun | None:
        """Get run by ID with eager loading of environment."""
        result = await self.session.execute(
            select(TestRun)
            .options(selectinload(TestRun.environment))
            .where(TestRun.run_id == run_id)
        )
        return result.scalar_one_or_none()

    async def update(self, run_id: UUID, update_data: RunUpdate) -> TestRun | None:
        """Update a run."""
        run = await self.get_by_id(run_id)
        if not run:
            return None
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(run, key, value)
        await self.session.flush()
        return run

    async def list_with_filters(
        self,
        status: str | None = None,
        test_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        fingerprint: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TestRun]:
        """List runs with advanced filters."""
        query = select(TestRun)
        conditions = []

        if status:
            conditions.append(TestRun.status == status)
        if test_name:
            conditions.append(TestRun.test_name.ilike(f"%{test_name}%"))
        if start_date:
            conditions.append(TestRun.start_time >= start_date)
        if end_date:
            conditions.append(TestRun.start_time <= end_date)

        if fingerprint:
            query = query.join(TestRun.environment)
            conditions.append(Environment.fingerprint_hash == fingerprint)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(TestRun.start_time.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
