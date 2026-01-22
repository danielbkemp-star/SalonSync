"""
SalonSync Models
"""

from app.models.user import User, UserRole
from app.models.salon import Salon
from app.models.staff import Staff, StaffStatus
from app.models.client import Client
from app.models.service import Service
from app.models.appointment import Appointment, AppointmentService, AppointmentStatus, AppointmentSource
from app.models.sale import Sale, SaleItem, Product, PaymentMethod, PaymentStatus
from app.models.media_set import MediaSet
from app.models.social_post import SocialPost, PostStatus, SocialPlatform

__all__ = [
    # User & Auth
    "User",
    "UserRole",
    # Salon (Multi-tenant)
    "Salon",
    # Staff
    "Staff",
    "StaffStatus",
    # Clients
    "Client",
    # Services
    "Service",
    # Appointments
    "Appointment",
    "AppointmentService",
    "AppointmentStatus",
    "AppointmentSource",
    # Sales & Payments
    "Sale",
    "SaleItem",
    "Product",
    "PaymentMethod",
    "PaymentStatus",
    # Media & Formula Vault
    "MediaSet",
    # Social Media
    "SocialPost",
    "PostStatus",
    "SocialPlatform",
]
