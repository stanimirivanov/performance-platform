"""Base repository with common CRUD operations."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository implementing common CRUD operations."""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, create_data: CreateSchemaType) -> ModelType:
        """Create a new record."""
        instance = self.model(**create_data.model_dump())
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get(self, id: UUID) -> ModelType | None:
        """Get a record by ID."""
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str | None = None,
    ) -> list[ModelType]:
        """List records with filters."""
        query = select(self.model)
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(self.model, key) == value)
        if order_by:
            query = query.order_by(getattr(self.model, order_by).desc())
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, id: UUID, update_data: UpdateSchemaType) -> ModelType | None:
        """Update a record."""
        instance = await self.get(id)
        if not instance:
            return None
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, id: UUID) -> bool:
        """Delete a record."""
        instance = await self.get(id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
