"""
User and Authentication schemas
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import BaseSchema, TimestampMixin


class UserBase(BaseSchema):
    """Base user fields"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8)
    role: Optional[str] = "Client"


class UserUpdate(BaseSchema):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    notification_email: Optional[bool] = None
    notification_sms: Optional[bool] = None


class UserResponse(UserBase, TimestampMixin):
    """Schema for user response"""
    id: int
    role: str
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email


class UserLogin(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user id
    email: str
    role: str
    exp: datetime
    iat: datetime


class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8)


class PasswordChange(BaseModel):
    """Password change request (when logged in)"""
    current_password: str
    new_password: str = Field(..., min_length=8)
