"""
Authentication API for SalonSync
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.app_settings import get_settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    verify_password_with_rehash_check,
)
from app.database import get_db
from app.models.user import User, UserRole

router = APIRouter()
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str | None = None
    phone: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from token."""
    from app.core.security import decode_token

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Require admin role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_staff(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Require staff role."""
    if not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required"
        )
    return current_user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """Login and get access token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is locked. Please try again later."
        )

    verify_result = verify_password_with_rehash_check(form_data.password, user.hashed_password)
    if not verify_result.verified:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.lock_account(minutes=30)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset failed attempts and update last login
    user.failed_login_attempts = 0
    user.locked_until = None
    from datetime import datetime
    user.last_login = datetime.utcnow()

    # Rehash password if needed (bcrypt -> argon2 migration)
    if verify_result.needs_rehash:
        user.hashed_password = get_password_hash(form_data.password)

    db.commit()

    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=UserRole.CLIENT,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user profile."""
    return current_user


@router.post("/logout")
async def logout():
    """Logout (client should discard token)."""
    return {"message": "Logged out successfully"}
