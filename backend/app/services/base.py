"""
Base service with common CRUD operations
"""

from typing import Generic, TypeVar, Type, Optional, List, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class with common CRUD operations.
    Inherit from this class to create model-specific services.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """Get a single record by ID"""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_field(
        self,
        db: AsyncSession,
        field: str,
        value: Any
    ) -> Optional[ModelType]:
        """Get a single record by a specific field"""
        result = await db.execute(
            select(self.model).where(getattr(self.model, field) == value)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "id",
        order_desc: bool = False,
        filters: Optional[dict] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and optional filters"""
        query = select(self.model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        # Apply ordering
        order_column = getattr(self.model, order_by, self.model.id)
        if order_desc:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_multi_by_salon(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[ModelType]:
        """Get records filtered by salon_id (multi-tenant)"""
        if not hasattr(self.model, 'salon_id'):
            raise ValueError(f"{self.model.__name__} does not have salon_id field")

        all_filters = {"salon_id": salon_id}
        if filters:
            all_filters.update(filters)

        return await self.get_multi(
            db, skip=skip, limit=limit, filters=all_filters
        )

    async def count(
        self,
        db: AsyncSession,
        filters: Optional[dict] = None
    ) -> int:
        """Count records with optional filters"""
        query = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        result = await db.execute(query)
        return result.scalar() or 0

    async def count_by_salon(
        self,
        db: AsyncSession,
        salon_id: int,
        filters: Optional[dict] = None
    ) -> int:
        """Count records for a specific salon"""
        all_filters = {"salon_id": salon_id}
        if filters:
            all_filters.update(filters)
        return await self.count(db, filters=all_filters)

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType
    ) -> ModelType:
        """Create a new record"""
        if hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump(exclude_unset=True)
        else:
            obj_data = dict(obj_in)

        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update an existing record"""
        if hasattr(obj_in, 'model_dump'):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = dict(obj_in)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> bool:
        """Delete a record by ID"""
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
            return True
        return False

    async def soft_delete(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[ModelType]:
        """Soft delete by setting is_active to False"""
        obj = await self.get(db, id)
        if obj and hasattr(obj, 'is_active'):
            obj.is_active = False
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        return None

    async def exists(
        self,
        db: AsyncSession,
        id: int
    ) -> bool:
        """Check if a record exists"""
        result = await db.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0
