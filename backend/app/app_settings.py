"""
SalonSync Configuration
Central configuration for the Salon Management System
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "SalonSync"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-in-production"

    # JWT Authentication
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1

    # Database
    DATABASE_URL: str = "postgresql://salonsync:salonsync@localhost:5432/salonsync"

    # Redis for caching and background tasks
    REDIS_URL: str = "redis://localhost:6379/0"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True

    # AI Services
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    # Media Storage (Cloudinary)
    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None

    # Social Media - Instagram
    INSTAGRAM_APP_ID: str | None = None
    INSTAGRAM_APP_SECRET: str | None = None

    # Social Media - TikTok
    TIKTOK_CLIENT_KEY: str | None = None
    TIKTOK_CLIENT_SECRET: str | None = None

    # Email Configuration
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str = "noreply@salonsync.com"

    # SMS Configuration (Twilio)
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_PHONE_NUMBER: str | None = None

    # Stripe Payment Processing
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    # Square Payment Processing (alternative)
    SQUARE_ACCESS_TOKEN: str | None = None
    SQUARE_LOCATION_ID: str | None = None

    # Frontend URL (for OAuth redirects)
    FRONTEND_URL: str = "http://localhost:5173"

    # Business Hours Defaults
    DEFAULT_OPENING_TIME: str = "09:00"
    DEFAULT_CLOSING_TIME: str = "19:00"
    APPOINTMENT_SLOT_DURATION_MINS: int = 15  # Booking slot granularity

    # Data storage
    DATA_DIR: Path = Path(__file__).parent.parent / "data"

    @property
    def is_cloud_deployment(self) -> bool:
        """Detect if running in cloud environment."""
        if os.getenv("RAILWAY_ENVIRONMENT"):
            return True
        if os.getenv("VERCEL"):
            return True
        if os.getenv("RENDER"):
            return True
        if os.getenv("CLOUD_DEPLOYMENT", "").lower() == "true":
            return True
        return False

    def validate_security_settings(self) -> None:
        """Validate security-critical settings."""
        import logging
        logger = logging.getLogger(__name__)

        if self.SECRET_KEY == "change-this-in-production":
            if self.is_cloud_deployment:
                raise RuntimeError(
                    "SECURITY ERROR: SECRET_KEY must be set to a secure random value in production!"
                )
            else:
                logger.warning(
                    "SECURITY WARNING: Using default SECRET_KEY. "
                    "Set SECRET_KEY environment variable for production."
                )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Service categories
SERVICE_CATEGORIES = [
    "Haircut",
    "Color",
    "Styling",
    "Treatment",
    "Extensions",
    "Nails",
    "Skincare",
    "Makeup",
    "Waxing",
    "Massage",
    "Other",
]

# Staff roles
STAFF_ROLES = [
    "Owner",
    "Manager",
    "Senior Stylist",
    "Stylist",
    "Junior Stylist",
    "Receptionist",
    "Assistant",
]

# Appointment statuses
APPOINTMENT_STATUSES = [
    "scheduled",
    "confirmed",
    "checked_in",
    "in_progress",
    "completed",
    "cancelled",
    "no_show",
]

# Payment methods
PAYMENT_METHODS = [
    "cash",
    "card",
    "gift_card",
    "loyalty_points",
    "split",
]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
