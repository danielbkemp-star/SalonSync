"""
Salon model for SalonSync
Multi-tenant support for salon businesses
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Salon(Base):
    """Salon business entity - the tenant in multi-tenant architecture"""
    __tablename__ = "salons"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)  # URL-friendly identifier
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    cover_photo_url = Column(String(500), nullable=True)

    # Contact
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)

    # Location
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), default="USA")
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    timezone = Column(String(50), default="America/New_York")

    # Business Hours (JSON stored separately or simplified)
    business_hours = Column(Text, nullable=True)  # JSON string of hours

    # Social Media
    instagram_handle = Column(String(100), nullable=True)
    instagram_access_token = Column(Text, nullable=True)
    instagram_user_id = Column(String(100), nullable=True)
    instagram_token_expires_at = Column(DateTime, nullable=True)

    tiktok_handle = Column(String(100), nullable=True)
    tiktok_access_token = Column(Text, nullable=True)
    tiktok_refresh_token = Column(Text, nullable=True)
    tiktok_open_id = Column(String(100), nullable=True)
    tiktok_token_expires_at = Column(DateTime, nullable=True)

    facebook_page_id = Column(String(100), nullable=True)
    facebook_access_token = Column(Text, nullable=True)

    # Payment Integration
    stripe_account_id = Column(String(255), nullable=True)
    stripe_onboarding_complete = Column(Boolean, default=False)
    stripe_charges_enabled = Column(Boolean, default=False)
    stripe_payouts_enabled = Column(Boolean, default=False)

    # Square (alternative payment)
    square_merchant_id = Column(String(255), nullable=True)
    square_access_token = Column(Text, nullable=True)
    square_location_id = Column(String(255), nullable=True)

    # Subscription & Billing
    subscription_tier = Column(String(50), default="free")  # free, starter, professional, enterprise
    subscription_status = Column(String(50), default="active")  # active, past_due, cancelled
    subscription_started_at = Column(DateTime, nullable=True)
    subscription_ends_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)

    # Feature Flags
    features_enabled = Column(Text, nullable=True)  # JSON array of enabled features

    # Settings
    booking_lead_time_hours = Column(Integer, default=2)  # Minimum advance booking time
    booking_window_days = Column(Integer, default=60)  # How far in advance clients can book
    cancellation_policy_hours = Column(Integer, default=24)  # Hours before appointment for free cancel
    deposit_required = Column(Boolean, default=False)
    deposit_percentage = Column(Numeric(5, 2), default=0)
    auto_confirm_appointments = Column(Boolean, default=True)
    send_confirmation_emails = Column(Boolean, default=True)
    send_reminder_emails = Column(Boolean, default=True)
    reminder_hours_before = Column(Integer, default=24)

    # Owner Reference
    owner_id = Column(Integer, nullable=True)  # FK to users.id - set up separately to avoid circular imports

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Admin verified legitimate business

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    staff = relationship("Staff", back_populates="salon")
    clients = relationship("Client", back_populates="salon")
    services = relationship("Service", back_populates="salon")
    appointments = relationship("Appointment", back_populates="salon")
    sales = relationship("Sale", back_populates="salon")
    media_sets = relationship("MediaSet", back_populates="salon")
    social_posts = relationship("SocialPost", back_populates="salon")
    gift_cards = relationship("GiftCard", back_populates="salon")

    def __repr__(self):
        return f"<Salon {self.id} - {self.name}>"

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        if self.city and self.state:
            parts.append(f"{self.city}, {self.state} {self.zip_code or ''}".strip())
        elif self.city:
            parts.append(self.city)
        return ", ".join(filter(None, parts))

    @property
    def has_social_connected(self) -> bool:
        """Check if any social media account is connected."""
        return bool(
            self.instagram_access_token or
            self.tiktok_access_token or
            self.facebook_access_token
        )

    @property
    def has_payments_enabled(self) -> bool:
        """Check if payment processing is set up."""
        return (
            (self.stripe_account_id and self.stripe_charges_enabled) or
            bool(self.square_access_token)
        )
