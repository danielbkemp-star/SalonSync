"""
Service schemas
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class ServiceCategory(BaseSchema):
    """Service category"""
    name: str
    description: Optional[str] = None
    display_order: int = 0
    service_count: int = 0


class ServiceBase(BaseSchema):
    """Base service fields"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str


class ServiceCreate(ServiceBase):
    """Schema for creating a service"""
    # salon_id is taken from URL path, not body

    # Pricing
    price: float = Field(..., ge=0)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    is_price_variable: bool = False

    # Duration
    duration_mins: int = Field(..., ge=5, le=480)
    buffer_before_mins: int = Field(0, ge=0, le=60)
    buffer_after_mins: int = Field(0, ge=0, le=60)
    processing_time_mins: int = Field(0, ge=0, le=180)

    # Availability
    is_active: bool = True
    is_online_bookable: bool = True
    requires_consultation: bool = False
    is_addon: bool = False

    # Staff requirements
    required_staff_count: int = Field(1, ge=1, le=4)
    skill_level_required: Optional[str] = None

    # Commission
    commission_type: str = "percentage"  # percentage, flat, none
    commission_value: Optional[float] = None

    # Display
    display_order: int = 0
    color: Optional[str] = None
    image_url: Optional[str] = None

    # Tags
    tags: List[str] = []


class ServiceUpdate(BaseSchema):
    """Schema for updating a service"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

    # Pricing
    price: Optional[float] = Field(None, ge=0)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    is_price_variable: Optional[bool] = None

    # Duration
    duration_mins: Optional[int] = Field(None, ge=5, le=480)
    buffer_before_mins: Optional[int] = Field(None, ge=0, le=60)
    buffer_after_mins: Optional[int] = Field(None, ge=0, le=60)
    processing_time_mins: Optional[int] = Field(None, ge=0, le=180)

    # Availability
    is_active: Optional[bool] = None
    is_online_bookable: Optional[bool] = None
    requires_consultation: Optional[bool] = None
    is_addon: Optional[bool] = None

    # Staff requirements
    required_staff_count: Optional[int] = Field(None, ge=1, le=4)
    skill_level_required: Optional[str] = None

    # Commission
    commission_type: Optional[str] = None
    commission_value: Optional[float] = None

    # Display
    display_order: Optional[int] = None
    color: Optional[str] = None
    image_url: Optional[str] = None

    # Tags
    tags: Optional[List[str]] = None


class ServiceResponse(ServiceBase, TimestampMixin):
    """Schema for service response"""
    id: int
    salon_id: int

    # Pricing
    price: float
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    is_price_variable: bool

    # Duration
    duration_mins: int
    buffer_before_mins: int
    buffer_after_mins: int
    processing_time_mins: int
    total_duration: int  # Computed property

    # Availability
    is_active: bool
    is_online_bookable: bool
    requires_consultation: bool
    is_addon: bool

    # Staff requirements
    required_staff_count: int
    skill_level_required: Optional[str] = None

    # Commission
    commission_type: str
    commission_value: Optional[float] = None

    # Display
    display_order: int
    color: Optional[str] = None
    image_url: Optional[str] = None

    # Tags
    tags: List[str] = []


class ServiceListResponse(PaginatedResponse[ServiceResponse]):
    """Paginated list of services"""
    pass


class ServicesByCategory(BaseSchema):
    """Services grouped by category"""
    category: str
    services: List[ServiceResponse]
