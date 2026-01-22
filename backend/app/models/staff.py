"""
Staff model for SalonSync
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class StaffStatus(str, enum.Enum):
    """Staff employment status"""
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class Staff(Base):
    """Staff member profile"""
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Professional Info
    title = Column(String(100), nullable=True)  # e.g., "Senior Stylist", "Color Specialist"
    bio = Column(Text, nullable=True)
    profile_photo_url = Column(String(500), nullable=True)
    specialties = Column(JSON, default=list)  # ["Color", "Extensions", "Curly Hair"]
    certifications = Column(JSON, default=list)  # Certifications and training
    years_experience = Column(Integer, nullable=True)

    # Social Media
    instagram_handle = Column(String(100), nullable=True)
    tiktok_handle = Column(String(100), nullable=True)
    portfolio_url = Column(String(500), nullable=True)

    # Employment
    status = Column(
        Enum(StaffStatus, values_callable=lambda x: [e.value for e in x]),
        default=StaffStatus.ACTIVE,
        index=True
    )
    hire_date = Column(DateTime, nullable=True)
    termination_date = Column(DateTime, nullable=True)

    # Commission & Pay
    commission_rate = Column(Numeric(5, 2), default=0)  # Percentage (e.g., 50.00 = 50%)
    hourly_rate = Column(Numeric(10, 2), nullable=True)
    salary = Column(Numeric(12, 2), nullable=True)

    # Schedule
    default_schedule = Column(JSON, default=dict)  # {"monday": {"start": "09:00", "end": "17:00"}, ...}
    accepts_walkins = Column(Boolean, default=True)
    booking_buffer_mins = Column(Integer, default=0)  # Buffer between appointments

    # Services
    service_ids = Column(JSON, default=list)  # Services this staff member can perform

    # Display
    display_order = Column(Integer, default=0)  # Order in staff list
    show_on_booking = Column(Boolean, default=True)  # Show on public booking page

    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    salon = relationship("Salon", back_populates="staff")
    user = relationship("User", back_populates="staff_profile")
    appointments = relationship("Appointment", back_populates="staff")
    media_sets = relationship("MediaSet", back_populates="staff")

    def __repr__(self):
        return f"<Staff {self.id} - {self.title}>"

    @property
    def full_name(self) -> str:
        """Get staff member's full name from user."""
        if self.user:
            return self.user.full_name
        return f"Staff #{self.id}"
