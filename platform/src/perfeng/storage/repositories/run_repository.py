"""Run repository with specialized queries."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TestRun
from ..schemas import RunCreate, RunUpdate
from .base import BaseRepository


class RunRepository(BaseRepository[TestRun, RunCreate, RunUpdate]):
    """Repository for TestRun operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(TestRun, session)

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

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(TestRun.start_time.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_environment(self, run_id: UUID) -> dict[str, Any] | None:
        """Get a run with its environment eagerly loaded."""
        result = await self.session.execute(
            select(TestRun)
            .options(selectinload(TestRun.environment))
            .where(TestRun.run_id == run_id)
        )
        return result.scalar_one_or_none()
