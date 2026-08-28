"""Base repository with common read/create/list/delete operations."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType]):
    """Base repository implementing common CRUD operations."""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

        mapper = inspect(model)
        if mapper is None:
            raise ValueError(f"Could not inspect model {model}")
        if len(mapper.primary_key) != 1:
            raise ValueError("Repository supports only models with a single primary key column")
        self.pk_column = mapper.primary_key[0]

    async def create(self, create_data: CreateSchemaType) -> ModelType:
        """Create a new record."""
        instance = self.model(**create_data.model_dump())
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get(self, id: UUID) -> ModelType | None:
        """Get a record by primary key."""
        result = await self.session.execute(select(self.model).where(self.pk_column == id))
        return result.scalar_one_or_none()

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str | None = None,
    ) -> list[ModelType]:
        """List records with optional filters."""
        query = select(self.model)
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(self.model, key) == value)
        if order_by:
            query = query.order_by(getattr(self.model, order_by).desc())
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete(self, id: UUID) -> bool:
        """Delete a record by primary key."""
        instance = await self.get(id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
