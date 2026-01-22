"""
Staff schemas
"""

from datetime import datetime, time
from typing import Optional, List, Dict

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class StaffScheduleDay(BaseSchema):
    """Schedule for a single day"""
    start: str = Field(..., pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")  # HH:MM
    end: str = Field(..., pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    is_working: bool = True


class StaffSchedule(BaseSchema):
    """Weekly schedule"""
    monday: Optional[StaffScheduleDay] = None
    tuesday: Optional[StaffScheduleDay] = None
    wednesday: Optional[StaffScheduleDay] = None
    thursday: Optional[StaffScheduleDay] = None
    friday: Optional[StaffScheduleDay] = None
    saturday: Optional[StaffScheduleDay] = None
    sunday: Optional[StaffScheduleDay] = None


class StaffBase(BaseSchema):
    """Base staff fields"""
    title: Optional[str] = None
    bio: Optional[str] = None
    specialties: List[str] = []
    certifications: List[str] = []
    years_experience: Optional[int] = Field(None, ge=0, le=60)

    # Social
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    portfolio_url: Optional[str] = None


class StaffCreate(StaffBase):
    """Schema for creating staff member"""
    user_id: int
    salon_id: int

    # Employment
    hire_date: Optional[datetime] = None
    commission_rate: Optional[float] = Field(None, ge=0, le=100)
    hourly_rate: Optional[float] = Field(None, ge=0)

    # Schedule
    default_schedule: Optional[Dict] = None
    accepts_walkins: bool = True
    booking_buffer_mins: int = Field(0, ge=0, le=60)

    # Services they can perform
    service_ids: List[int] = []

    # Display
    show_on_booking: bool = True


class StaffUpdate(BaseSchema):
    """Schema for updating staff member"""
    title: Optional[str] = None
    bio: Optional[str] = None
    profile_photo_url: Optional[str] = None
    specialties: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    years_experience: Optional[int] = None

    # Social
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    portfolio_url: Optional[str] = None

    # Employment
    status: Optional[str] = None
    commission_rate: Optional[float] = Field(None, ge=0, le=100)
    hourly_rate: Optional[float] = Field(None, ge=0)

    # Schedule
    default_schedule: Optional[Dict] = None
    accepts_walkins: Optional[bool] = None
    booking_buffer_mins: Optional[int] = Field(None, ge=0, le=60)

    # Services
    service_ids: Optional[List[int]] = None

    # Display
    display_order: Optional[int] = None
    show_on_booking: Optional[bool] = None


class StaffResponse(StaffBase, TimestampMixin):
    """Schema for staff response"""
    id: int
    salon_id: int
    user_id: int

    # From user
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_photo_url: Optional[str] = None

    # Employment
    status: str
    hire_date: Optional[datetime] = None
    commission_rate: Optional[float] = None

    # Schedule
    default_schedule: Optional[Dict] = None
    accepts_walkins: bool
    booking_buffer_mins: int

    # Services
    service_ids: List[int] = []

    # Display
    display_order: int
    show_on_booking: bool


class StaffListResponse(PaginatedResponse[StaffResponse]):
    """Paginated list of staff"""
    pass


class StaffAvailability(BaseSchema):
    """Staff availability for a specific date"""
    staff_id: int
    date: datetime
    available_slots: List[Dict[str, str]]  # [{"start": "09:00", "end": "09:30"}, ...]
    booked_slots: List[Dict[str, str]]


class StaffPerformance(BaseSchema):
    """Staff performance metrics"""
    staff_id: int
    period_start: datetime
    period_end: datetime

    total_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    no_shows: int

    total_revenue: float
    average_ticket: float
    total_tips: float

    new_clients_served: int
    returning_clients_served: int

    average_rating: Optional[float] = None
    total_reviews: int = 0
