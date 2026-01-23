"""
SalonSync Waitlist API
Endpoints for managing the appointment waitlist.
"""

from datetime import datetime, date, time, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.salon import Salon
from app.models.client import Client
from app.models.waitlist import WaitlistEntry, WaitlistStatus, WaitlistPriority
from app.services import notification_service

router = APIRouter()


# ==================== SCHEMAS ====================

class WaitlistCreate(BaseModel):
    """Create a waitlist entry."""
    client_id: Optional[int] = None
    client_name: str = Field(..., min_length=1, max_length=100)
    client_email: Optional[EmailStr] = None
    client_phone: Optional[str] = None

    service_id: Optional[int] = None
    staff_id: Optional[int] = None

    preferred_date: date
    preferred_time_start: Optional[time] = None
    preferred_time_end: Optional[time] = None
    flexible_dates: bool = False
    flexible_staff: bool = True

    notes: Optional[str] = None
    priority: str = "normal"
    notification_preference: str = "both"


class WaitlistUpdate(BaseModel):
    """Update a waitlist entry."""
    preferred_date: Optional[date] = None
    preferred_time_start: Optional[time] = None
    preferred_time_end: Optional[time] = None
    flexible_dates: Optional[bool] = None
    flexible_staff: Optional[bool] = None
    staff_id: Optional[int] = None
    service_id: Optional[int] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class WaitlistResponse(BaseModel):
    """Waitlist entry response."""
    id: int
    salon_id: int
    client_id: Optional[int]
    client_name: str
    client_email: Optional[str]
    client_phone: Optional[str]
    service_id: Optional[int]
    service_name: Optional[str] = None
    staff_id: Optional[int]
    staff_name: Optional[str] = None
    preferred_date: date
    preferred_time_start: Optional[time]
    preferred_time_end: Optional[time]
    flexible_dates: bool
    flexible_staff: bool
    status: str
    priority: str
    notes: Optional[str]
    internal_notes: Optional[str]
    notification_count: int
    last_notified_at: Optional[datetime]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class WaitlistStats(BaseModel):
    """Waitlist statistics."""
    total_pending: int
    total_notified: int
    total_booked_this_week: int
    avg_wait_days: float
    entries_by_service: List[dict]


# ==================== ENDPOINTS ====================

@router.post("/salons/{salon_id}/waitlist", response_model=WaitlistResponse)
async def create_waitlist_entry(
    salon_id: int,
    entry_data: WaitlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a client to the waitlist."""
    # Verify salon
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Validate contact info
    if not entry_data.client_email and not entry_data.client_phone:
        raise HTTPException(
            status_code=400,
            detail="At least one contact method (email or phone) is required"
        )

    # Check for existing similar entry
    existing = db.query(WaitlistEntry).filter(
        WaitlistEntry.salon_id == salon_id,
        WaitlistEntry.client_email == entry_data.client_email,
        WaitlistEntry.preferred_date == entry_data.preferred_date,
        WaitlistEntry.status.in_([WaitlistStatus.PENDING, WaitlistStatus.NOTIFIED]),
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Client is already on the waitlist for this date"
        )

    # Create entry
    entry = WaitlistEntry(
        salon_id=salon_id,
        client_id=entry_data.client_id,
        client_name=entry_data.client_name,
        client_email=entry_data.client_email,
        client_phone=entry_data.client_phone,
        service_id=entry_data.service_id,
        staff_id=entry_data.staff_id,
        preferred_date=entry_data.preferred_date,
        preferred_time_start=entry_data.preferred_time_start,
        preferred_time_end=entry_data.preferred_time_end,
        flexible_dates=entry_data.flexible_dates,
        flexible_staff=entry_data.flexible_staff,
        notes=entry_data.notes,
        priority=WaitlistPriority(entry_data.priority),
        notification_preference=entry_data.notification_preference,
        expires_at=datetime.combine(entry_data.preferred_date + timedelta(days=7), time.max),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return _entry_to_response(entry)


@router.get("/salons/{salon_id}/waitlist", response_model=List[WaitlistResponse])
async def list_waitlist(
    salon_id: int,
    status_filter: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    staff_id: Optional[int] = None,
    service_id: Optional[int] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List waitlist entries for a salon."""
    query = db.query(WaitlistEntry).filter(WaitlistEntry.salon_id == salon_id)

    if status_filter:
        query = query.filter(WaitlistEntry.status == status_filter)

    if active_only:
        query = query.filter(
            WaitlistEntry.status.in_([WaitlistStatus.PENDING, WaitlistStatus.NOTIFIED]),
            WaitlistEntry.preferred_date >= date.today(),
        )

    if date_from:
        query = query.filter(WaitlistEntry.preferred_date >= date_from)

    if date_to:
        query = query.filter(WaitlistEntry.preferred_date <= date_to)

    if staff_id:
        query = query.filter(WaitlistEntry.staff_id == staff_id)

    if service_id:
        query = query.filter(WaitlistEntry.service_id == service_id)

    entries = query.order_by(
        WaitlistEntry.priority.desc(),
        WaitlistEntry.preferred_date,
        WaitlistEntry.created_at
    ).offset(skip).limit(limit).all()

    return [_entry_to_response(e) for e in entries]


@router.get("/salons/{salon_id}/waitlist/{entry_id}", response_model=WaitlistResponse)
async def get_waitlist_entry(
    salon_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific waitlist entry."""
    entry = db.query(WaitlistEntry).filter(
        WaitlistEntry.id == entry_id,
        WaitlistEntry.salon_id == salon_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")

    return _entry_to_response(entry)


@router.patch("/salons/{salon_id}/waitlist/{entry_id}", response_model=WaitlistResponse)
async def update_waitlist_entry(
    salon_id: int,
    entry_id: int,
    update_data: WaitlistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a waitlist entry."""
    entry = db.query(WaitlistEntry).filter(
        WaitlistEntry.id == entry_id,
        WaitlistEntry.salon_id == salon_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        if key == "priority" and value:
            value = WaitlistPriority(value)
        if key == "status" and value:
            value = WaitlistStatus(value)
        setattr(entry, key, value)

    db.commit()
    db.refresh(entry)

    return _entry_to_response(entry)


@router.delete("/salons/{salon_id}/waitlist/{entry_id}")
async def delete_waitlist_entry(
    salon_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a waitlist entry."""
    entry = db.query(WaitlistEntry).filter(
        WaitlistEntry.id == entry_id,
        WaitlistEntry.salon_id == salon_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")

    entry.cancel()
    db.commit()

    return {"message": "Waitlist entry cancelled"}


@router.post("/salons/{salon_id}/waitlist/{entry_id}/notify")
async def notify_waitlist_entry(
    salon_id: int,
    entry_id: int,
    message: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send notification to a waitlist client about availability."""
    entry = db.query(WaitlistEntry).filter(
        WaitlistEntry.id == entry_id,
        WaitlistEntry.salon_id == salon_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")

    if not entry.is_active:
        raise HTTPException(status_code=400, detail="Waitlist entry is not active")

    salon = db.query(Salon).filter(Salon.id == salon_id).first()

    # Send notification
    result = {"email": False, "sms": False}

    default_message = message or f"Great news! An appointment slot has opened up at {salon.name} on {entry.preferred_date.strftime('%B %d, %Y')}. Contact us to book!"

    if entry.notification_preference in ["email", "both"] and entry.client_email:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7c3aed;">Good News from {salon.name}!</h2>
            <p>Hi {entry.client_name},</p>
            <p>{default_message}</p>
            <p>Call us at {salon.phone or 'our phone'} or book online to secure your spot!</p>
            <p>Best,<br>{salon.name} Team</p>
        </div>
        """
        result["email"] = notification_service.send_email(
            to_email=entry.client_email,
            subject=f"Appointment Available at {salon.name}!",
            html_content=html_content
        )

    if entry.notification_preference in ["sms", "both"] and entry.client_phone:
        result["sms"] = notification_service.send_sms(
            to_phone=entry.client_phone,
            message=default_message
        )

    # Update entry
    entry.mark_notified()
    db.commit()

    return {
        "message": "Notification sent",
        "email_sent": result["email"],
        "sms_sent": result["sms"],
        "notification_count": entry.notification_count,
    }


@router.post("/salons/{salon_id}/waitlist/{entry_id}/book")
async def book_from_waitlist(
    salon_id: int,
    entry_id: int,
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a waitlist entry as booked with an appointment."""
    entry = db.query(WaitlistEntry).filter(
        WaitlistEntry.id == entry_id,
        WaitlistEntry.salon_id == salon_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")

    entry.mark_booked(appointment_id)
    db.commit()

    return {"message": "Waitlist entry marked as booked", "appointment_id": appointment_id}


@router.get("/salons/{salon_id}/waitlist/stats", response_model=WaitlistStats)
async def get_waitlist_stats(
    salon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get waitlist statistics."""
    from sqlalchemy import func
    from app.models.service import Service

    today = date.today()
    week_ago = today - timedelta(days=7)

    # Counts
    pending = db.query(func.count(WaitlistEntry.id)).filter(
        WaitlistEntry.salon_id == salon_id,
        WaitlistEntry.status == WaitlistStatus.PENDING,
        WaitlistEntry.preferred_date >= today,
    ).scalar() or 0

    notified = db.query(func.count(WaitlistEntry.id)).filter(
        WaitlistEntry.salon_id == salon_id,
        WaitlistEntry.status == WaitlistStatus.NOTIFIED,
        WaitlistEntry.preferred_date >= today,
    ).scalar() or 0

    booked_this_week = db.query(func.count(WaitlistEntry.id)).filter(
        WaitlistEntry.salon_id == salon_id,
        WaitlistEntry.status == WaitlistStatus.BOOKED,
        WaitlistEntry.updated_at >= datetime.combine(week_ago, time.min),
    ).scalar() or 0

    # Average wait time for booked entries
    booked_entries = db.query(WaitlistEntry).filter(
        WaitlistEntry.salon_id == salon_id,
        WaitlistEntry.status == WaitlistStatus.BOOKED,
    ).limit(100).all()

    avg_wait = 0.0
    if booked_entries:
        wait_days = [
            (e.updated_at - e.created_at).days
            for e in booked_entries
            if e.updated_at
        ]
        avg_wait = sum(wait_days) / len(wait_days) if wait_days else 0

    # Entries by service
    service_stats = db.query(
        Service.name,
        func.count(WaitlistEntry.id).label("count")
    ).join(WaitlistEntry, WaitlistEntry.service_id == Service.id).filter(
        WaitlistEntry.salon_id == salon_id,
        WaitlistEntry.status.in_([WaitlistStatus.PENDING, WaitlistStatus.NOTIFIED]),
    ).group_by(Service.name).all()

    return WaitlistStats(
        total_pending=pending,
        total_notified=notified,
        total_booked_this_week=booked_this_week,
        avg_wait_days=round(avg_wait, 1),
        entries_by_service=[{"service": s.name, "count": s.count} for s in service_stats],
    )


@router.get("/salons/{salon_id}/waitlist/for-date/{target_date}")
async def get_waitlist_for_date(
    salon_id: int,
    target_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get waitlist entries for a specific date (useful when a slot opens up)."""
    entries = db.query(WaitlistEntry).filter(
        WaitlistEntry.salon_id == salon_id,
        WaitlistEntry.status.in_([WaitlistStatus.PENDING, WaitlistStatus.NOTIFIED]),
        WaitlistEntry.preferred_date == target_date,
    ).order_by(WaitlistEntry.priority.desc(), WaitlistEntry.created_at).all()

    # Also check flexible entries
    flexible_entries = db.query(WaitlistEntry).filter(
        WaitlistEntry.salon_id == salon_id,
        WaitlistEntry.status.in_([WaitlistStatus.PENDING, WaitlistStatus.NOTIFIED]),
        WaitlistEntry.flexible_dates == True,
        WaitlistEntry.preferred_date.between(target_date - timedelta(days=3), target_date + timedelta(days=3)),
    ).order_by(WaitlistEntry.priority.desc(), WaitlistEntry.created_at).all()

    all_entries = entries + [e for e in flexible_entries if e not in entries]

    return [_entry_to_response(e) for e in all_entries]


# ==================== HELPER FUNCTIONS ====================

def _entry_to_response(entry: WaitlistEntry) -> WaitlistResponse:
    """Convert waitlist entry to response."""
    return WaitlistResponse(
        id=entry.id,
        salon_id=entry.salon_id,
        client_id=entry.client_id,
        client_name=entry.client_name,
        client_email=entry.client_email,
        client_phone=entry.client_phone,
        service_id=entry.service_id,
        service_name=entry.service.name if entry.service else None,
        staff_id=entry.staff_id,
        staff_name=entry.staff.full_name if entry.staff else None,
        preferred_date=entry.preferred_date,
        preferred_time_start=entry.preferred_time_start,
        preferred_time_end=entry.preferred_time_end,
        flexible_dates=entry.flexible_dates,
        flexible_staff=entry.flexible_staff,
        status=entry.status.value,
        priority=entry.priority.value,
        notes=entry.notes,
        internal_notes=entry.internal_notes,
        notification_count=entry.notification_count,
        last_notified_at=entry.last_notified_at,
        created_at=entry.created_at,
        is_active=entry.is_active,
    )
