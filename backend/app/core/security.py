"""
Security utilities for SalonSync
JWT token creation/validation and password hashing
Uses Argon2 for new passwords with bcrypt fallback for legacy hashes
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, NamedTuple, Optional, Union

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from jose import JWTError, jwt

from app.app_settings import get_settings

# Argon2 password hasher with secure defaults
ph = PasswordHasher()


class PasswordVerifyResult(NamedTuple):
    """Result of password verification with migration flag."""
    verified: bool
    needs_rehash: bool


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    result = verify_password_with_rehash_check(plain_password, hashed_password)
    return result.verified


def verify_password_with_rehash_check(plain_password: str, hashed_password: str) -> PasswordVerifyResult:
    """Verify password and indicate if hash should be upgraded."""
    if not plain_password or not hashed_password:
        return PasswordVerifyResult(verified=False, needs_rehash=False)

    # Check if this is a bcrypt hash (legacy)
    if hashed_password.startswith(('$2a$', '$2b$', '$2y$')):
        return _verify_bcrypt_password(plain_password, hashed_password)

    return _verify_argon2_password(plain_password, hashed_password)


def _verify_argon2_password(plain_password: str, hashed_password: str) -> PasswordVerifyResult:
    """Verify an Argon2 hashed password."""
    try:
        ph.verify(hashed_password, plain_password)
        needs_rehash = ph.check_needs_rehash(hashed_password)
        return PasswordVerifyResult(verified=True, needs_rehash=needs_rehash)
    except (VerifyMismatchError, InvalidHashError):
        return PasswordVerifyResult(verified=False, needs_rehash=False)
    except Exception:
        return PasswordVerifyResult(verified=False, needs_rehash=False)


def _verify_bcrypt_password(plain_password: str, hashed_password: str) -> PasswordVerifyResult:
    """Verify a legacy bcrypt hashed password."""
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        if bcrypt.checkpw(password_bytes, hash_bytes):
            return PasswordVerifyResult(verified=True, needs_rehash=True)
        return PasswordVerifyResult(verified=False, needs_rehash=False)
    except Exception:
        return PasswordVerifyResult(verified=False, needs_rehash=False)


def create_access_token(subject: Union[str, int], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    settings = get_settings()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token."""
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def generate_password_reset_token(email: str) -> str:
    """Generate a password reset token."""
    settings = get_settings()
    delta = timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta

    to_encode = {
        "exp": expires,
        "sub": email,
        "type": "password_reset"
    }
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and extract the email."""
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def generate_email_verification_token(email: str) -> str:
    """Generate an email verification token."""
    settings = get_settings()
    delta = timedelta(hours=48)
    now = datetime.now(timezone.utc)
    expires = now + delta

    to_encode = {
        "exp": expires,
        "sub": email,
        "type": "email_verification"
    }
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_email_verification_token(token: str) -> Optional[str]:
    """Verify an email verification token and extract the email."""
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "email_verification":
            return None
        return payload.get("sub")
    except JWTError:
        return None
