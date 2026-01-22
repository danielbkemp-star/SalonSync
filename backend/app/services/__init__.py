"""
SalonSync Services - Business Logic Layer
"""

from app.services.base import BaseService
from app.services.salon import SalonService
from app.services.staff import StaffService
from app.services.client import ClientService
from app.services.service import ServiceService
from app.services.appointment import AppointmentService
from app.services.media_set import MediaSetService
from app.services.social_post import SocialPostService
from app.services.cloudinary import CloudinaryService
from app.services.ai_caption import AICaptionService

# Phase 3 - Differentiator Services
from app.services.media_service import MediaService, media_service
from app.services.content_service import ContentService, content_service
from app.services.instagram_service import InstagramService, instagram_service
from app.services.payment_service import PaymentService, payment_service
from app.services.scheduling_service import SchedulingService, scheduling_service

__all__ = [
    # Base
    "BaseService",
    # Core Services
    "SalonService",
    "StaffService",
    "ClientService",
    "ServiceService",
    "AppointmentService",
    "MediaSetService",
    "SocialPostService",
    "CloudinaryService",
    "AICaptionService",
    # Differentiator Services (Phase 3)
    "MediaService",
    "media_service",
    "ContentService",
    "content_service",
    "InstagramService",
    "instagram_service",
    "PaymentService",
    "payment_service",
    "SchedulingService",
    "scheduling_service",
]
