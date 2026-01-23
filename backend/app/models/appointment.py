"""
Appointment model for SalonSync
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AppointmentStatus(str, enum.Enum):
    """Appointment status"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class AppointmentSource(str, enum.Enum):
    """How the appointment was booked"""
    ONLINE = "online"
    PHONE = "phone"
    WALK_IN = "walk_in"
    RECURRING = "recurring"
    REBOOK = "rebook"


class Appointment(Base):
    """Appointment booking"""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    # Salon Reference
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)

    # Core References
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)

    # Timing
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    duration_mins = Column(Integer, nullable=False)

    # Status
    status = Column(
        Enum(AppointmentStatus, values_callable=lambda x: [e.value for e in x]),
        default=AppointmentStatus.SCHEDULED,
        index=True
    )
    source = Column(
        Enum(AppointmentSource, values_callable=lambda x: [e.value for e in x]),
        default=AppointmentSource.ONLINE
    )

    # Check-in Tracking
    checked_in_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Pricing
    estimated_total = Column(Numeric(10, 2), nullable=True)
    final_total = Column(Numeric(10, 2), nullable=True)
    deposit_amount = Column(Numeric(10, 2), default=0)
    deposit_paid = Column(Boolean, default=False)

    # Notes
    client_notes = Column(Text, nullable=True)  # Notes from client during booking
    staff_notes = Column(Text, nullable=True)  # Private notes for staff
    internal_notes = Column(Text, nullable=True)  # Admin notes

    # Confirmation
    confirmation_sent = Column(Boolean, default=False)
    confirmation_sent_at = Column(DateTime, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)

    # Cancellation
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(String(50), nullable=True)  # client, staff, system
    cancellation_reason = Column(Text, nullable=True)
    cancellation_fee = Column(Numeric(10, 2), default=0)

    # Recurring
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(JSON, nullable=True)  # {"frequency": "weekly", "day": "monday"}
    parent_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    # Colors and Display
    color = Column(String(20), nullable=True)  # Override calendar color

    # Online Booking
    confirmation_code = Column(String(20), nullable=True, index=True)  # For client lookup

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    salon = relationship("Salon", back_populates="appointments")
    client = relationship("Client", back_populates="appointments")
    staff = relationship("Staff", back_populates="appointments")
    services = relationship("AppointmentService", back_populates="appointment", cascade="all, delete-orphan")
    parent_appointment = relationship("Appointment", remote_side=[id], foreign_keys=[parent_appointment_id])
    media_set = relationship("MediaSet", back_populates="appointment", uselist=False)

    def __repr__(self):
        return f"<Appointment {self.id} - {self.start_time}>"


class AppointmentService(Base):
    """Services included in an appointment (many-to-many with extra data)"""
    __tablename__ = "appointment_services"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)

    # Pricing at time of booking (may differ from current service price)
    price = Column(Numeric(10, 2), nullable=False)
    duration_mins = Column(Integer, nullable=False)

    # Order within appointment
    sequence = Column(Integer, default=0)

    # Relationships
    appointment = relationship("Appointment", back_populates="services")
    service = relationship("Service", back_populates="appointments")

    def __repr__(self):
        return f"<AppointmentService {self.appointment_id} - {self.service_id}>"
