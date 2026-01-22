"""
API Dependencies for SalonSync
Common dependencies for authentication and authorization
"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models import User, Salon, Staff, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


async def get_current_user_optional(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Require superuser/admin role."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_owner_role(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Require owner role or higher."""
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required"
        )
    return current_user


def require_manager_role(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Require manager role or higher."""
    allowed_roles = [UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER]
    if current_user.role not in allowed_roles and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return current_user


def require_stylist_role(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Require stylist role or higher."""
    allowed_roles = [UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER, UserRole.STYLIST]
    if current_user.role not in allowed_roles and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Stylist access required"
        )
    return current_user


def require_staff_role(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Require any staff role (not client)."""
    if current_user.role == UserRole.CLIENT and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required"
        )
    return current_user


class SalonAccess:
    """Dependency for verifying salon access."""

    def __init__(self, require_owner: bool = False, require_manager: bool = False):
        self.require_owner = require_owner
        self.require_manager = require_manager

    async def __call__(
        self,
        salon_id: int,
        current_user: Annotated[User, Depends(get_current_user)],
        db: Session = Depends(get_db)
    ) -> Salon:
        """Verify user has access to the specified salon."""
        # Superusers have access to all salons
        if current_user.is_superuser:
            salon = db.query(Salon).filter(Salon.id == salon_id).first()
            if not salon:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Salon not found"
                )
            return salon

        # Check if user has staff profile for this salon
        staff = db.query(Staff).filter(
            Staff.user_id == current_user.id,
            Staff.salon_id == salon_id
        ).first()

        if not staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this salon"
            )

        # Check role requirements
        if self.require_owner:
            if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Owner access required for this action"
                )

        if self.require_manager:
            if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Manager access required for this action"
                )

        salon = db.query(Salon).filter(Salon.id == salon_id).first()
        if not salon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salon not found"
            )

        return salon


# Pre-configured dependency instances
require_salon_access = SalonAccess()
require_salon_owner = SalonAccess(require_owner=True)
require_salon_manager = SalonAccess(require_manager=True)


async def get_user_salon(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> Optional[Salon]:
    """Get the primary salon for the current user."""
    # Find staff profile
    staff = db.query(Staff).filter(Staff.user_id == current_user.id).first()
    if staff:
        return db.query(Salon).filter(Salon.id == staff.salon_id).first()
    return None


async def get_user_staff_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> Optional[Staff]:
    """Get the staff profile for the current user."""
    return db.query(Staff).filter(Staff.user_id == current_user.id).first()


def require_staff_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> Staff:
    """Require user to have a staff profile."""
    staff = db.query(Staff).filter(Staff.user_id == current_user.id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff profile required"
        )
    return staff


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[Optional[User], Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(require_admin)]
OwnerUser = Annotated[User, Depends(require_owner_role)]
ManagerUser = Annotated[User, Depends(require_manager_role)]
StylistUser = Annotated[User, Depends(require_stylist_role)]
StaffUser = Annotated[User, Depends(require_staff_role)]
UserStaffProfile = Annotated[Staff, Depends(require_staff_profile)]
