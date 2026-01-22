"""
Salon schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class SalonBase(BaseSchema):
    """Base salon fields"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    # Location
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "USA"
    timezone: str = "America/New_York"


class SalonCreate(SalonBase):
    """Schema for creating a salon"""
    slug: Optional[str] = None  # Auto-generated if not provided

    @field_validator('slug', mode='before')
    @classmethod
    def generate_slug(cls, v, info):
        if not v and 'name' in info.data:
            from slugify import slugify
            return slugify(info.data['name'])
        return v


class SalonUpdate(BaseSchema):
    """Schema for updating a salon"""
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    cover_photo_url: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    # Location
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    timezone: Optional[str] = None

    # Social handles (not tokens)
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None


class SalonSettings(BaseSchema):
    """Salon booking and business settings"""
    booking_lead_time_hours: Optional[int] = Field(None, ge=0, le=168)
    booking_window_days: Optional[int] = Field(None, ge=1, le=365)
    cancellation_policy_hours: Optional[int] = Field(None, ge=0, le=168)
    deposit_required: Optional[bool] = None
    deposit_percentage: Optional[float] = Field(None, ge=0, le=100)
    auto_confirm_appointments: Optional[bool] = None
    send_confirmation_emails: Optional[bool] = None
    send_reminder_emails: Optional[bool] = None
    reminder_hours_before: Optional[int] = Field(None, ge=1, le=72)


class SalonSocialConnect(BaseSchema):
    """Schema for connecting social media accounts"""
    platform: str = Field(..., pattern="^(instagram|tiktok|facebook)$")
    auth_code: str
    redirect_uri: str


class SalonSocialStatus(BaseSchema):
    """Status of connected social accounts"""
    instagram_connected: bool = False
    instagram_handle: Optional[str] = None
    instagram_expires_at: Optional[datetime] = None

    tiktok_connected: bool = False
    tiktok_handle: Optional[str] = None
    tiktok_expires_at: Optional[datetime] = None

    facebook_connected: bool = False


class SalonPaymentStatus(BaseSchema):
    """Status of payment integration"""
    stripe_connected: bool = False
    stripe_charges_enabled: bool = False
    stripe_payouts_enabled: bool = False

    square_connected: bool = False


class SalonResponse(SalonBase, TimestampMixin):
    """Schema for salon response"""
    id: int
    slug: str
    logo_url: Optional[str] = None
    cover_photo_url: Optional[str] = None

    # Social (public handles only)
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None

    # Subscription
    subscription_tier: str
    subscription_status: str

    # Status
    is_active: bool
    is_verified: bool

    # Computed
    full_address: Optional[str] = None
    has_social_connected: bool = False
    has_payments_enabled: bool = False


class SalonListResponse(PaginatedResponse[SalonResponse]):
    """Paginated list of salons"""
    pass


class SalonStats(BaseSchema):
    """Salon statistics"""
    total_clients: int
    total_staff: int
    total_appointments_today: int
    total_revenue_today: float
    total_revenue_week: float
    total_revenue_month: float
    appointments_completed_today: int
    new_clients_this_month: int
