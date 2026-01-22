"""
Client model for SalonSync
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Client(Base):
    """Client profile"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)

    # Contact Info (can exist without user account)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True, index=True)
    phone_secondary = Column(String(50), nullable=True)

    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)

    # Preferences
    preferred_staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    preferred_services = Column(JSON, default=list)
    communication_preference = Column(String(20), default="email")  # email, sms, both
    marketing_opt_in = Column(Boolean, default=False)

    # Social Media
    instagram_handle = Column(String(100), nullable=True)
    tiktok_handle = Column(String(100), nullable=True)

    # Hair/Beauty Profile
    hair_type = Column(String(50), nullable=True)  # fine, medium, coarse
    hair_color = Column(String(50), nullable=True)  # natural color
    current_hair_color = Column(String(100), nullable=True)  # current/processed color
    hair_texture = Column(String(50), nullable=True)  # straight, wavy, curly, coily
    hair_length = Column(String(50), nullable=True)  # short, medium, long
    hair_density = Column(String(50), nullable=True)  # thin, medium, thick
    hair_porosity = Column(String(50), nullable=True)  # low, medium, high
    hair_color_history = Column(JSON, default=list)  # Previous colors/treatments
    skin_type = Column(String(50), nullable=True)
    skin_tone = Column(String(50), nullable=True)
    allergies = Column(Text, nullable=True)
    scalp_conditions = Column(Text, nullable=True)
    special_notes = Column(Text, nullable=True)

    # Consents - Critical for photo usage!
    photo_consent = Column(Boolean, default=False)  # Can salon keep photos
    social_media_consent = Column(Boolean, default=False)  # Can post to social media
    website_consent = Column(Boolean, default=False)  # Can use on website/portfolio
    sms_consent = Column(Boolean, default=False)  # Can send SMS
    consent_updated_at = Column(DateTime, nullable=True)

    # Loyalty
    loyalty_points = Column(Integer, default=0)
    loyalty_tier = Column(String(50), default="bronze")  # bronze, silver, gold, platinum
    referral_code = Column(String(20), unique=True, nullable=True)
    referred_by_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    # Financials
    total_spent = Column(Numeric(12, 2), default=0)
    average_ticket = Column(Numeric(10, 2), default=0)
    outstanding_balance = Column(Numeric(10, 2), default=0)

    # Stats
    visit_count = Column(Integer, default=0)
    last_visit = Column(DateTime, nullable=True)
    next_appointment = Column(DateTime, nullable=True)
    cancellation_count = Column(Integer, default=0)
    no_show_count = Column(Integer, default=0)

    # Important Dates
    birthday = Column(DateTime, nullable=True)
    anniversary = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_vip = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    blocked_reason = Column(Text, nullable=True)

    # Tags for segmentation
    tags = Column(JSON, default=list)

    # Metadata
    source = Column(String(50), nullable=True)  # walk_in, referral, online, etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    salon = relationship("Salon", back_populates="clients")
    user = relationship("User", back_populates="client_profile")
    preferred_staff = relationship("Staff", foreign_keys=[preferred_staff_id])
    referred_by = relationship("Client", remote_side=[id], foreign_keys=[referred_by_id])
    appointments = relationship("Appointment", back_populates="client")
    sales = relationship("Sale", back_populates="client")
    media_sets = relationship("MediaSet", back_populates="client")

    def __repr__(self):
        return f"<Client {self.id} - {self.full_name}>"

    @property
    def full_name(self) -> str:
        """Get client's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or "Unknown"
