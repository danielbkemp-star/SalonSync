"""
User model for SalonSync
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles for SalonSync"""
    ADMIN = "Admin"  # System administrator
    OWNER = "Owner"
    MANAGER = "Manager"
    SENIOR_STYLIST = "Senior Stylist"
    STYLIST = "Stylist"
    JUNIOR_STYLIST = "Junior Stylist"
    RECEPTIONIST = "Receptionist"
    ASSISTANT = "Assistant"
    CLIENT = "Client"


class User(Base):
    """User account for SalonSync"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    # Profile
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Role and Permissions
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.CLIENT,
        index=True
    )
    permissions = Column(JSON, default=list)

    # Session & Activity Tracking
    last_login = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)
    last_ip_address = Column(String(45), nullable=True)

    # Preferences
    preferences = Column(JSON, default=dict)
    notification_email = Column(Boolean, default=True)
    notification_sms = Column(Boolean, default=True)

    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Security
    password_reset_token = Column(String(500), nullable=True, unique=True)
    password_reset_expires = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    must_change_password = Column(Boolean, default=False)

    # Relationships
    staff_profile = relationship("Staff", back_populates="user", uselist=False)
    client_profile = relationship("Client", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email

    @property
    def is_staff(self) -> bool:
        """Check if user is a staff member."""
        return self.role not in [UserRole.CLIENT]

    @property
    def is_admin(self) -> bool:
        """Check if user is admin (Owner or Manager)."""
        return self.role in [UserRole.OWNER, UserRole.MANAGER] or self.is_superuser

    @property
    def can_book_appointments(self) -> bool:
        """Check if user can book appointments for clients."""
        return self.role in [UserRole.OWNER, UserRole.MANAGER, UserRole.RECEPTIONIST]

    @property
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until

    def lock_account(self, minutes: int = 30):
        """Lock account for specified minutes."""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)

    def unlock_account(self):
        """Unlock account."""
        self.locked_until = None
        self.failed_login_attempts = 0
