"""
Staff API for SalonSync
"""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.api.auth import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.models.staff import Staff, StaffStatus

router = APIRouter()


class StaffResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    status: str
    specialties: List[str]
    accepts_walkins: bool
    show_on_booking: bool
    full_name: str

    class Config:
        from_attributes = True


class StaffUpdate(BaseModel):
    title: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    status: Optional[str] = None
    commission_rate: Optional[float] = None
    accepts_walkins: Optional[bool] = None
    show_on_booking: Optional[bool] = None
    default_schedule: Optional[dict] = None


@router.get("/", response_model=List[StaffResponse])
async def list_staff(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    active_only: bool = True,
    show_on_booking: Optional[bool] = None,
):
    """List all staff members."""
    query = db.query(Staff).options(joinedload(Staff.user))

    if active_only:
        query = query.filter(Staff.status == StaffStatus.ACTIVE)

    if show_on_booking is not None:
        query = query.filter(Staff.show_on_booking == show_on_booking)

    query = query.order_by(Staff.display_order, Staff.id)
    return query.all()


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Get a specific staff member."""
    staff = db.query(Staff).options(joinedload(Staff.user)).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    return staff


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: int,
    staff_data: StaffUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Update a staff member (admin only)."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )

    update_data = staff_data.model_dump(exclude_unset=True)

    # Convert status string to enum if provided
    if "status" in update_data:
        update_data["status"] = StaffStatus(update_data["status"])

    for field, value in update_data.items():
        setattr(staff, field, value)

    db.commit()
    db.refresh(staff)
    return staff


@router.get("/{staff_id}/schedule")
async def get_staff_schedule(
    staff_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Get a staff member's schedule."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    return staff.default_schedule or {}
