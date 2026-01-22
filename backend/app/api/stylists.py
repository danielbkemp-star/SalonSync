"""
Stylists API Routes for SalonSync
CRUD operations for staff/stylists within a salon
"""

from datetime import datetime, date, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Salon, Staff, Appointment, Service
from app.models.staff import StaffStatus
from app.models.appointment import AppointmentStatus
from app.schemas.staff import (
    StaffCreate, StaffUpdate, StaffResponse, StaffListResponse,
    StaffAvailability, StaffPerformance
)
from app.schemas.base import MessageResponse, PaginatedResponse
from app.api.dependencies import (
    CurrentUser, require_salon_access, SalonAccess
)

router = APIRouter()


# ============================================================================
# CRUD Operations
# ============================================================================

@router.post("/salons/{salon_id}/stylists", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_stylist(
    salon_id: int,
    staff_in: StaffCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Create a new stylist/staff member.

    Requires manager role or higher.
    """
    salon = await SalonAccess(require_manager=True)(salon_id, current_user, db)

    # Verify user exists
    user = db.query(User).filter(User.id == staff_in.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user already has staff profile in this salon
    existing = db.query(Staff).filter(
        Staff.user_id == staff_in.user_id,
        Staff.salon_id == salon_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a staff profile in this salon"
        )

    # Create staff profile
    staff = Staff(
        salon_id=salon_id,
        user_id=staff_in.user_id,
        title=staff_in.title,
        bio=staff_in.bio,
        specialties=staff_in.specialties,
        certifications=staff_in.certifications,
        years_experience=staff_in.years_experience,
        instagram_handle=staff_in.instagram_handle,
        tiktok_handle=staff_in.tiktok_handle,
        portfolio_url=staff_in.portfolio_url,
        hire_date=staff_in.hire_date,
        commission_rate=staff_in.commission_rate,
        hourly_rate=staff_in.hourly_rate,
        default_schedule=staff_in.default_schedule,
        accepts_walkins=staff_in.accepts_walkins,
        booking_buffer_mins=staff_in.booking_buffer_mins,
        service_ids=staff_in.service_ids,
        show_on_booking=staff_in.show_on_booking,
        status=StaffStatus.ACTIVE,
    )

    db.add(staff)
    db.commit()
    db.refresh(staff)

    return _staff_to_response(staff)


@router.get("/salons/{salon_id}/stylists", response_model=StaffListResponse)
async def list_stylists(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    show_on_booking: Optional[bool] = None,
):
    """
    List all stylists/staff in a salon.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    query = db.query(Staff).filter(Staff.salon_id == salon_id)

    if status:
        query = query.filter(Staff.status == status)

    if show_on_booking is not None:
        query = query.filter(Staff.show_on_booking == show_on_booking)

    total = query.count()
    staff_members = query.order_by(Staff.display_order, Staff.id).offset(skip).limit(limit).all()

    items = [_staff_to_response(s) for s in staff_members]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/stylists/{stylist_id}", response_model=StaffResponse)
async def get_stylist(
    stylist_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get stylist by ID."""
    staff = db.query(Staff).filter(Staff.id == stylist_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )

    # Verify access
    await require_salon_access(staff.salon_id, current_user, db)

    return _staff_to_response(staff)


@router.put("/stylists/{stylist_id}", response_model=StaffResponse)
async def update_stylist(
    stylist_id: int,
    staff_in: StaffUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update stylist details.

    Requires manager role or the stylist themselves.
    """
    staff = db.query(Staff).filter(Staff.id == stylist_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )

    # Check permissions - manager or self
    is_self = staff.user_id == current_user.id
    if not is_self:
        await SalonAccess(require_manager=True)(staff.salon_id, current_user, db)

    # Update fields
    update_data = staff_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(staff, field, value)

    staff.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(staff)

    return _staff_to_response(staff)


@router.delete("/stylists/{stylist_id}")
async def delete_stylist(
    stylist_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Remove stylist from salon.

    Requires owner role. Sets status to terminated rather than hard delete.
    """
    staff = db.query(Staff).filter(Staff.id == stylist_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )

    await SalonAccess(require_owner=True)(staff.salon_id, current_user, db)

    staff.status = StaffStatus.TERMINATED
    staff.termination_date = datetime.utcnow()
    staff.show_on_booking = False
    staff.updated_at = datetime.utcnow()

    db.commit()

    return MessageResponse(message="Stylist removed successfully")


# ============================================================================
# Availability
# ============================================================================

@router.get("/stylists/{stylist_id}/availability", response_model=StaffAvailability)
async def get_stylist_availability(
    stylist_id: int,
    current_user: CurrentUser,
    date: date = Query(..., description="Date to check availability"),
    db: Session = Depends(get_db)
):
    """
    Get stylist availability for a specific date.

    Returns available time slots and booked appointments.
    """
    staff = db.query(Staff).filter(Staff.id == stylist_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )

    await require_salon_access(staff.salon_id, current_user, db)

    # Get day of week
    day_name = date.strftime("%A").lower()

    # Get schedule for this day
    schedule = staff.default_schedule or {}
    day_schedule = schedule.get(day_name)

    available_slots = []
    booked_slots = []

    if day_schedule and day_schedule.get("is_working", True):
        start_time = day_schedule.get("start", "09:00")
        end_time = day_schedule.get("end", "17:00")

        # Get booked appointments for this day
        start_dt = datetime.combine(date, datetime.strptime(start_time, "%H:%M").time())
        end_dt = datetime.combine(date, datetime.strptime(end_time, "%H:%M").time())

        appointments = db.query(Appointment).filter(
            Appointment.staff_id == stylist_id,
            Appointment.start_time >= start_dt,
            Appointment.start_time < end_dt,
            Appointment.status.notin_([AppointmentStatus.CANCELLED])
        ).order_by(Appointment.start_time).all()

        # Build booked slots
        for appt in appointments:
            booked_slots.append({
                "start": appt.start_time.strftime("%H:%M"),
                "end": appt.end_time.strftime("%H:%M")
            })

        # Build available slots (simplified - 30 min intervals)
        current = start_dt
        slot_duration = timedelta(minutes=30)

        while current + slot_duration <= end_dt:
            slot_end = current + slot_duration
            slot_start_str = current.strftime("%H:%M")
            slot_end_str = slot_end.strftime("%H:%M")

            # Check if slot overlaps with any booked appointment
            is_available = True
            for appt in appointments:
                if current < appt.end_time and slot_end > appt.start_time:
                    is_available = False
                    break

            if is_available:
                available_slots.append({
                    "start": slot_start_str,
                    "end": slot_end_str
                })

            current = slot_end

    return StaffAvailability(
        staff_id=stylist_id,
        date=datetime.combine(date, datetime.min.time()),
        available_slots=available_slots,
        booked_slots=booked_slots
    )


# ============================================================================
# Performance
# ============================================================================

@router.get("/stylists/{stylist_id}/performance", response_model=StaffPerformance)
async def get_stylist_performance(
    stylist_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    start_date: date = Query(...),
    end_date: date = Query(...),
):
    """
    Get stylist performance metrics for a date range.

    Requires manager role or the stylist themselves.
    """
    staff = db.query(Staff).filter(Staff.id == stylist_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )

    # Check permissions
    is_self = staff.user_id == current_user.id
    if not is_self:
        await SalonAccess(require_manager=True)(staff.salon_id, current_user, db)

    # Convert dates to datetime
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # Query appointments
    appointments = db.query(Appointment).filter(
        Appointment.staff_id == stylist_id,
        Appointment.start_time >= start_dt,
        Appointment.start_time <= end_dt
    )

    total_appointments = appointments.count()

    completed = appointments.filter(
        Appointment.status == AppointmentStatus.COMPLETED
    ).count()

    cancelled = appointments.filter(
        Appointment.status == AppointmentStatus.CANCELLED
    ).count()

    no_shows = appointments.filter(
        Appointment.status == AppointmentStatus.NO_SHOW
    ).count()

    # Revenue (from completed appointments with final_total)
    from app.models import Sale
    revenue_result = db.query(func.sum(Sale.total)).filter(
        Sale.staff_id == stylist_id,
        Sale.created_at >= start_dt,
        Sale.created_at <= end_dt,
        Sale.payment_status == "completed"
    ).scalar() or 0

    tips_result = db.query(func.sum(Sale.tip_amount)).filter(
        Sale.staff_id == stylist_id,
        Sale.created_at >= start_dt,
        Sale.created_at <= end_dt
    ).scalar() or 0

    avg_ticket = float(revenue_result) / completed if completed > 0 else 0

    # Client counts (simplified)
    # Would need to track new vs returning properly
    new_clients = 0
    returning_clients = completed

    return StaffPerformance(
        staff_id=stylist_id,
        period_start=start_dt,
        period_end=end_dt,
        total_appointments=total_appointments,
        completed_appointments=completed,
        cancelled_appointments=cancelled,
        no_shows=no_shows,
        total_revenue=float(revenue_result),
        average_ticket=avg_ticket,
        total_tips=float(tips_result),
        new_clients_served=new_clients,
        returning_clients_served=returning_clients,
    )


# ============================================================================
# Services
# ============================================================================

@router.get("/stylists/{stylist_id}/services")
async def get_stylist_services(
    stylist_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get services that this stylist can perform."""
    staff = db.query(Staff).filter(Staff.id == stylist_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )

    await require_salon_access(staff.salon_id, current_user, db)

    service_ids = staff.service_ids or []

    if not service_ids:
        # If no services specified, return all salon services
        services = db.query(Service).filter(
            Service.salon_id == staff.salon_id,
            Service.is_active == True
        ).all()
    else:
        services = db.query(Service).filter(
            Service.id.in_(service_ids),
            Service.is_active == True
        ).all()

    return {"services": services}


@router.put("/stylists/{stylist_id}/services")
async def update_stylist_services(
    stylist_id: int,
    service_ids: List[int],
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update services that this stylist can perform."""
    staff = db.query(Staff).filter(Staff.id == stylist_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )

    await SalonAccess(require_manager=True)(staff.salon_id, current_user, db)

    # Verify all services belong to salon
    valid_services = db.query(Service.id).filter(
        Service.id.in_(service_ids),
        Service.salon_id == staff.salon_id
    ).all()
    valid_ids = [s[0] for s in valid_services]

    staff.service_ids = valid_ids
    staff.updated_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message=f"Updated {len(valid_ids)} services")


# ============================================================================
# Helper Functions
# ============================================================================

def _staff_to_response(staff: Staff) -> StaffResponse:
    """Convert Staff model to StaffResponse schema."""
    return StaffResponse(
        id=staff.id,
        salon_id=staff.salon_id,
        user_id=staff.user_id,
        full_name=staff.full_name,
        email=staff.user.email if staff.user else None,
        phone=staff.user.phone if staff.user else None,
        avatar_url=staff.user.avatar_url if staff.user and hasattr(staff.user, 'avatar_url') else None,
        profile_photo_url=staff.profile_photo_url,
        title=staff.title,
        bio=staff.bio,
        specialties=staff.specialties or [],
        certifications=staff.certifications or [],
        years_experience=staff.years_experience,
        instagram_handle=staff.instagram_handle,
        tiktok_handle=staff.tiktok_handle,
        portfolio_url=staff.portfolio_url,
        status=staff.status.value if staff.status else "active",
        hire_date=staff.hire_date,
        commission_rate=float(staff.commission_rate) if staff.commission_rate else None,
        default_schedule=staff.default_schedule,
        accepts_walkins=staff.accepts_walkins,
        booking_buffer_mins=staff.booking_buffer_mins or 0,
        service_ids=staff.service_ids or [],
        display_order=staff.display_order or 0,
        show_on_booking=staff.show_on_booking,
        created_at=staff.created_at,
        updated_at=staff.updated_at,
    )
