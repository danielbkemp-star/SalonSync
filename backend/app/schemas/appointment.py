"""
Appointment schemas
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class AppointmentServiceItem(BaseSchema):
    """Service item within an appointment"""
    service_id: int
    price: Optional[float] = None  # Override price, if None uses service default
    duration_mins: Optional[int] = None  # Override duration
    sequence: int = 0


class AppointmentBase(BaseSchema):
    """Base appointment fields"""
    client_id: int
    staff_id: int
    start_time: datetime


class AppointmentCreate(AppointmentBase):
    """Schema for creating an appointment"""
    salon_id: int

    # Services
    services: List[AppointmentServiceItem]

    # Source
    source: str = "online"  # online, phone, walk_in, recurring, rebook

    # Notes
    client_notes: Optional[str] = None

    # Deposit
    deposit_amount: Optional[float] = Field(None, ge=0)

    # Recurring
    is_recurring: bool = False
    recurring_pattern: Optional[dict] = None  # {"frequency": "weekly", "day": "monday", "end_date": "..."}


class AppointmentUpdate(BaseSchema):
    """Schema for updating an appointment"""
    staff_id: Optional[int] = None
    start_time: Optional[datetime] = None

    # Services
    services: Optional[List[AppointmentServiceItem]] = None

    # Notes
    client_notes: Optional[str] = None
    staff_notes: Optional[str] = None
    internal_notes: Optional[str] = None

    # Pricing
    estimated_total: Optional[float] = None


class AppointmentStatusUpdate(BaseSchema):
    """Schema for updating appointment status"""
    status: str = Field(..., pattern="^(scheduled|confirmed|checked_in|in_progress|completed|cancelled|no_show)$")
    notes: Optional[str] = None

    # For cancellation
    cancellation_reason: Optional[str] = None
    cancellation_fee: Optional[float] = Field(None, ge=0)


class AppointmentReschedule(BaseSchema):
    """Schema for rescheduling an appointment"""
    new_start_time: datetime
    new_staff_id: Optional[int] = None
    notify_client: bool = True
    reason: Optional[str] = None


class AppointmentCheckout(BaseSchema):
    """Schema for checkout/completing an appointment"""
    final_total: float = Field(..., ge=0)
    payment_method: str  # cash, card, gift_card, split
    tip_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

    # For split payments
    split_payments: Optional[List[dict]] = None  # [{"method": "card", "amount": 50}, ...]


class AppointmentServiceResponse(BaseSchema):
    """Service within appointment response"""
    id: int
    service_id: int
    service_name: str
    price: float
    duration_mins: int
    sequence: int


class AppointmentResponse(AppointmentBase, TimestampMixin):
    """Schema for appointment response"""
    id: int
    salon_id: int

    # Timing
    end_time: datetime
    duration_mins: int

    # Status
    status: str
    source: str

    # Check-in tracking
    checked_in_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Pricing
    estimated_total: Optional[float] = None
    final_total: Optional[float] = None
    deposit_amount: float
    deposit_paid: bool

    # Notes
    client_notes: Optional[str] = None
    staff_notes: Optional[str] = None

    # Confirmation
    confirmation_sent: bool
    reminder_sent: bool

    # Cancellation
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    # Recurring
    is_recurring: bool

    # Display
    color: Optional[str] = None

    # Services
    services: List[AppointmentServiceResponse] = []

    # Expanded relations (optional)
    client_name: Optional[str] = None
    staff_name: Optional[str] = None


class AppointmentListResponse(PaginatedResponse[AppointmentResponse]):
    """Paginated list of appointments"""
    pass


class AppointmentSlot(BaseSchema):
    """Available appointment slot"""
    start_time: datetime
    end_time: datetime
    staff_id: int
    staff_name: str


class AvailableSlotsRequest(BaseSchema):
    """Request for available slots"""
    salon_id: int
    service_ids: List[int]
    date: datetime
    staff_id: Optional[int] = None  # If None, check all staff


class AvailableSlotsResponse(BaseSchema):
    """Available slots response"""
    date: datetime
    slots: List[AppointmentSlot]


class DailySchedule(BaseSchema):
    """Daily schedule overview"""
    date: datetime
    appointments: List[AppointmentResponse]
    total_appointments: int
    total_revenue: float
    utilization_percent: float  # How booked the day is
