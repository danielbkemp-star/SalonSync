"""
Client schemas
"""

from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class ClientHairProfile(BaseSchema):
    """Hair profile information"""
    hair_type: Optional[str] = None  # fine, medium, coarse
    hair_color: Optional[str] = None  # natural color
    current_hair_color: Optional[str] = None
    hair_texture: Optional[str] = None  # straight, wavy, curly, coily
    hair_length: Optional[str] = None  # short, medium, long
    hair_density: Optional[str] = None  # thin, medium, thick
    hair_porosity: Optional[str] = None  # low, medium, high
    hair_color_history: List[str] = []  # Previous colors/treatments
    scalp_conditions: Optional[str] = None
    allergies: Optional[str] = None


class ClientConsent(BaseSchema):
    """Client consent settings"""
    photo_consent: bool = False
    social_media_consent: bool = False
    website_consent: bool = False
    sms_consent: bool = False
    marketing_opt_in: bool = False


class ClientBase(BaseSchema):
    """Base client fields"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    # Social
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None


class ClientCreate(ClientBase):
    """Schema for creating a client"""
    salon_id: int

    # Contact
    phone_secondary: Optional[str] = None

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    # Preferences
    preferred_staff_id: Optional[int] = None
    communication_preference: str = "email"  # email, sms, both

    # Hair profile
    hair_profile: Optional[ClientHairProfile] = None

    # Consent
    consent: Optional[ClientConsent] = None

    # Notes
    special_notes: Optional[str] = None

    # Important dates
    birthday: Optional[date] = None

    # Source
    source: Optional[str] = None  # walk_in, referral, online, etc.
    referred_by_id: Optional[int] = None


class ClientUpdate(BaseSchema):
    """Schema for updating a client"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    # Social
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None

    # Preferences
    preferred_staff_id: Optional[int] = None
    communication_preference: Optional[str] = None

    # Hair profile (individual fields)
    hair_type: Optional[str] = None
    hair_color: Optional[str] = None
    current_hair_color: Optional[str] = None
    hair_texture: Optional[str] = None
    hair_length: Optional[str] = None
    hair_density: Optional[str] = None
    hair_porosity: Optional[str] = None
    scalp_conditions: Optional[str] = None
    allergies: Optional[str] = None

    # Consent
    photo_consent: Optional[bool] = None
    social_media_consent: Optional[bool] = None
    website_consent: Optional[bool] = None
    sms_consent: Optional[bool] = None
    marketing_opt_in: Optional[bool] = None

    # Notes
    special_notes: Optional[str] = None

    # Status
    is_vip: Optional[bool] = None
    tags: Optional[List[str]] = None

    # Important dates
    birthday: Optional[date] = None


class ClientResponse(ClientBase, TimestampMixin):
    """Schema for client response"""
    id: int
    salon_id: int
    user_id: Optional[int] = None

    # Full name helper
    full_name: str

    # Contact
    phone_secondary: Optional[str] = None

    # Address
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    # Preferences
    preferred_staff_id: Optional[int] = None
    communication_preference: str

    # Hair profile
    hair_type: Optional[str] = None
    hair_color: Optional[str] = None
    current_hair_color: Optional[str] = None
    hair_texture: Optional[str] = None

    # Consent
    photo_consent: bool
    social_media_consent: bool
    marketing_opt_in: bool

    # Loyalty
    loyalty_points: int
    loyalty_tier: str

    # Stats
    visit_count: int
    total_spent: float
    last_visit: Optional[datetime] = None
    next_appointment: Optional[datetime] = None

    # Status
    is_active: bool
    is_vip: bool
    tags: List[str] = []

    # Important dates
    birthday: Optional[date] = None

    # Source
    source: Optional[str] = None


class ClientListResponse(PaginatedResponse[ClientResponse]):
    """Paginated list of clients"""
    pass


class ClientSearch(BaseSchema):
    """Client search parameters"""
    query: Optional[str] = None  # Search name, email, phone
    tags: Optional[List[str]] = None
    is_vip: Optional[bool] = None
    loyalty_tier: Optional[str] = None
    has_upcoming_appointment: Optional[bool] = None
    last_visit_after: Optional[datetime] = None
    last_visit_before: Optional[datetime] = None


class ClientHistory(BaseSchema):
    """Client service history"""
    client_id: int
    appointments: List[dict]  # Recent appointments
    total_visits: int
    total_spent: float
    favorite_services: List[str]
    favorite_staff: Optional[str] = None
    hair_color_history: List[str] = []
