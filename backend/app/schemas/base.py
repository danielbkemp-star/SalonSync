"""
Base schemas and common patterns for SalonSync
"""

from datetime import datetime
from typing import Generic, TypeVar, Optional, List

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for created_at and updated_at fields"""
    created_at: datetime
    updated_at: Optional[datetime] = None


# Generic type for paginated responses
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    code: Optional[str] = None
