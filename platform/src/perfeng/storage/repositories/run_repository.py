"""Run repository with specialized queries."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Environment, TestRun
from ..schemas import RunCreate, RunUpdate
from .base import BaseRepository


class RunRepository(BaseRepository[TestRun, RunCreate, RunUpdate]):
    """Repository for TestRun operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(TestRun, session)
        # Set the ID field name for the base repository
        self.model.id = TestRun.run_id  # type: ignore

    async def get_by_id(self, run_id: UUID) -> TestRun | None:
        """Get run by ID with eager loading."""
        result = await self.session.execute(
            select(TestRun)
            .options(selectinload(TestRun.environment))
            .where(TestRun.run_id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_with_environment(self, run_id: UUID) -> dict[str, Any] | None:
        """Get run with environment as a dict."""
        run = await self.get_by_id(run_id)
        if not run:
            return None
        return {"run": run, "environment": run.environment}

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

        # fingerprint filter requires join with environment
        if fingerprint:
            query = query.join(TestRun.environment)
            conditions.append(Environment.fingerprint_hash == fingerprint)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(TestRun.start_time.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
