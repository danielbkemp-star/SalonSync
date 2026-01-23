"""
SalonSync Waitlist Model
For managing appointment waitlist entries.
"""

import enum
from datetime import datetime, date

from sqlalchemy import Column, Integer, String, DateTime, Date, Time, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class WaitlistStatus(str, enum.Enum):
    PENDING = "pending"
    NOTIFIED = "notified"
    BOOKED = "booked"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class WaitlistPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    VIP = "vip"


class WaitlistEntry(Base):
    """
    Waitlist entry for clients who want to be notified
    when their preferred appointment time becomes available.
    """
    __tablename__ = "waitlist_entries"

    id = Column(Integer, primary_key=True, index=True)
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    # Contact info (for non-registered clients)
    client_name = Column(String(100), nullable=False)
    client_email = Column(String(255), nullable=True)
    client_phone = Column(String(20), nullable=True)

    # Preferred appointment details
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)  # Preferred staff (optional)

    # Date/time preferences
    preferred_date = Column(Date, nullable=False)
    preferred_time_start = Column(Time, nullable=True)  # Start of preferred time window
    preferred_time_end = Column(Time, nullable=True)    # End of preferred time window
    flexible_dates = Column(Boolean, default=False)     # Accept nearby dates
    flexible_staff = Column(Boolean, default=True)      # Accept any available staff

    # Status tracking
    status = Column(Enum(WaitlistStatus), default=WaitlistStatus.PENDING, nullable=False)
    priority = Column(Enum(WaitlistPriority), default=WaitlistPriority.NORMAL, nullable=False)

    # Notes
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Staff-only notes

    # Notification tracking
    notification_count = Column(Integer, default=0)
    last_notified_at = Column(DateTime, nullable=True)
    notification_preference = Column(String(20), default="both")  # email, sms, both

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Auto-expire old entries

    # If booked, link to the appointment
    booked_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    # Relationships
    salon = relationship("Salon", backref="waitlist_entries")
    client = relationship("Client", backref="waitlist_entries")
    service = relationship("Service")
    staff = relationship("Staff")
    booked_appointment = relationship("Appointment")

    @property
    def is_active(self) -> bool:
        """Check if entry is still active."""
        if self.status not in [WaitlistStatus.PENDING, WaitlistStatus.NOTIFIED]:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        if self.preferred_date < date.today():
            return False
        return True

    @property
    def contact_display(self) -> str:
        """Get display string for contact info."""
        if self.client_email and self.client_phone:
            return f"{self.client_email} / {self.client_phone}"
        return self.client_email or self.client_phone or "No contact"

    def mark_notified(self):
        """Mark entry as notified."""
        self.status = WaitlistStatus.NOTIFIED
        self.notification_count += 1
        self.last_notified_at = datetime.utcnow()

    def mark_booked(self, appointment_id: int):
        """Mark entry as booked."""
        self.status = WaitlistStatus.BOOKED
        self.booked_appointment_id = appointment_id
        self.updated_at = datetime.utcnow()

    def cancel(self):
        """Cancel the waitlist entry."""
        self.status = WaitlistStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f"<WaitlistEntry {self.id}: {self.client_name} for {self.preferred_date}>"
