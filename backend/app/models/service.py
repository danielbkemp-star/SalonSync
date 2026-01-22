"""
Service model for SalonSync
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Service(Base):
    """Service offered by the salon"""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)

    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)  # Haircut, Color, Styling, etc.

    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    price_min = Column(Numeric(10, 2), nullable=True)  # For "starting at" pricing
    price_max = Column(Numeric(10, 2), nullable=True)  # For price ranges
    is_price_variable = Column(Boolean, default=False)  # Price determined at checkout

    # Duration
    duration_mins = Column(Integer, nullable=False, default=30)
    buffer_before_mins = Column(Integer, default=0)  # Prep time
    buffer_after_mins = Column(Integer, default=0)  # Cleanup time
    processing_time_mins = Column(Integer, default=0)  # e.g., color processing

    # Availability
    is_active = Column(Boolean, default=True)
    is_online_bookable = Column(Boolean, default=True)
    requires_consultation = Column(Boolean, default=False)
    is_addon = Column(Boolean, default=False)  # Add-on service only

    # Staff Requirements
    required_staff_count = Column(Integer, default=1)  # For services needing multiple staff
    skill_level_required = Column(String(50), nullable=True)  # senior, junior, any

    # Commission
    commission_type = Column(String(20), default="percentage")  # percentage, flat, none
    commission_value = Column(Numeric(10, 2), nullable=True)

    # Display
    display_order = Column(Integer, default=0)
    color = Column(String(20), nullable=True)  # For calendar display
    image_url = Column(String(500), nullable=True)

    # Tags and Search
    tags = Column(JSON, default=list)
    search_keywords = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    salon = relationship("Salon", back_populates="services")
    appointments = relationship("AppointmentService", back_populates="service")

    def __repr__(self):
        return f"<Service {self.id} - {self.name}>"

    @property
    def total_duration(self) -> int:
        """Get total time slot needed including buffers."""
        return self.duration_mins + self.buffer_before_mins + self.buffer_after_mins
