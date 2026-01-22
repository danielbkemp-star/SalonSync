"""
SalonSync Pydantic Schemas
"""

from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    Token, TokenPayload, PasswordReset, PasswordChange
)
from app.schemas.salon import (
    SalonCreate, SalonUpdate, SalonResponse, SalonListResponse,
    SalonSettings, SalonSocialConnect
)
from app.schemas.staff import (
    StaffCreate, StaffUpdate, StaffResponse, StaffListResponse,
    StaffSchedule, StaffAvailability
)
from app.schemas.client import (
    ClientCreate, ClientUpdate, ClientResponse, ClientListResponse,
    ClientHairProfile, ClientConsent
)
from app.schemas.service import (
    ServiceCreate, ServiceUpdate, ServiceResponse, ServiceListResponse,
    ServiceCategory
)
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentListResponse, AppointmentStatusUpdate, AppointmentReschedule
)
from app.schemas.media_set import (
    MediaSetCreate, MediaSetUpdate, MediaSetResponse, MediaSetListResponse,
    ColorFormula, ProductUsed, PhotoUpload
)
from app.schemas.social_post import (
    SocialPostCreate, SocialPostUpdate, SocialPostResponse,
    SocialPostListResponse, SocialPostSchedule, CaptionGenerate
)

__all__ = [
    # Base
    "BaseSchema", "TimestampMixin", "PaginatedResponse",
    # User/Auth
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "Token", "TokenPayload", "PasswordReset", "PasswordChange",
    # Salon
    "SalonCreate", "SalonUpdate", "SalonResponse", "SalonListResponse",
    "SalonSettings", "SalonSocialConnect",
    # Staff
    "StaffCreate", "StaffUpdate", "StaffResponse", "StaffListResponse",
    "StaffSchedule", "StaffAvailability",
    # Client
    "ClientCreate", "ClientUpdate", "ClientResponse", "ClientListResponse",
    "ClientHairProfile", "ClientConsent",
    # Service
    "ServiceCreate", "ServiceUpdate", "ServiceResponse", "ServiceListResponse",
    "ServiceCategory",
    # Appointment
    "AppointmentCreate", "AppointmentUpdate", "AppointmentResponse",
    "AppointmentListResponse", "AppointmentStatusUpdate", "AppointmentReschedule",
    # MediaSet
    "MediaSetCreate", "MediaSetUpdate", "MediaSetResponse", "MediaSetListResponse",
    "ColorFormula", "ProductUsed", "PhotoUpload",
    # SocialPost
    "SocialPostCreate", "SocialPostUpdate", "SocialPostResponse",
    "SocialPostListResponse", "SocialPostSchedule", "CaptionGenerate",
]
