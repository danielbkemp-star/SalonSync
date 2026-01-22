"""
Appointments API Routes for SalonSync
CRUD operations and calendar views for appointments
"""

from datetime import datetime, date, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models import Appointment, AppointmentService, Service, Client, Staff
from app.models.appointment import AppointmentStatus, AppointmentSource
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentListResponse,
    AppointmentStatusUpdate, AppointmentReschedule, AppointmentCheckout,
    AvailableSlotsRequest, AvailableSlotsResponse, AppointmentSlot, DailySchedule
)
from app.schemas.base import MessageResponse, PaginatedResponse
from app.api.dependencies import (
    CurrentUser, require_salon_access, SalonAccess
)

router = APIRouter()


# ============================================================================
# CRUD Operations
# ============================================================================

@router.post("/salons/{salon_id}/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    salon_id: int,
    appt_in: AppointmentCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Book a new appointment.

    Calculates total duration and price from selected services.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    # Verify client and staff belong to salon
    client = db.query(Client).filter(
        Client.id == appt_in.client_id,
        Client.salon_id == salon_id
    ).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found in this salon"
        )

    staff = db.query(Staff).filter(
        Staff.id == appt_in.staff_id,
        Staff.salon_id == salon_id
    ).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff not found in this salon"
        )

    # Calculate total duration and price from services
    total_duration = 0
    total_price = 0
    services_to_add = []

    for svc_item in appt_in.services:
        service = db.query(Service).filter(
            Service.id == svc_item.service_id,
            Service.salon_id == salon_id
        ).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Service {svc_item.service_id} not found"
            )

        price = svc_item.price if svc_item.price is not None else float(service.price)
        duration = svc_item.duration_mins if svc_item.duration_mins else service.total_duration
        total_duration += duration
        total_price += price
        services_to_add.append((service, price, duration, svc_item.sequence))

    # Calculate end time
    end_time = appt_in.start_time + timedelta(minutes=total_duration)

    # Check for conflicts
    conflict = db.query(Appointment).filter(
        Appointment.staff_id == appt_in.staff_id,
        Appointment.status.notin_([AppointmentStatus.CANCELLED]),
        Appointment.start_time < end_time,
        Appointment.end_time > appt_in.start_time
    ).first()

    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot conflicts with existing appointment"
        )

    # Create appointment
    appointment = Appointment(
        salon_id=salon_id,
        client_id=appt_in.client_id,
        staff_id=appt_in.staff_id,
        start_time=appt_in.start_time,
        end_time=end_time,
        duration_mins=total_duration,
        status=AppointmentStatus.SCHEDULED,
        source=AppointmentSource(appt_in.source),
        estimated_total=total_price,
        client_notes=appt_in.client_notes,
        deposit_amount=appt_in.deposit_amount or 0,
        is_recurring=appt_in.is_recurring,
        recurring_pattern=appt_in.recurring_pattern,
        created_by_id=current_user.id,
    )

    db.add(appointment)
    db.flush()

    # Add services
    for service, price, duration, sequence in services_to_add:
        appt_service = AppointmentService(
            appointment_id=appointment.id,
            service_id=service.id,
            price=price,
            duration_mins=duration,
            sequence=sequence,
        )
        db.add(appt_service)

    db.commit()
    db.refresh(appointment)

    return _appointment_to_response(appointment, db)


@router.get("/salons/{salon_id}/appointments", response_model=AppointmentListResponse)
async def list_appointments(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    staff_id: Optional[int] = None,
    client_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """List appointments with filters."""
    salon = await require_salon_access(salon_id, current_user, db)

    query = db.query(Appointment).filter(Appointment.salon_id == salon_id)

    if start_date:
        query = query.filter(Appointment.start_time >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.filter(Appointment.start_time <= datetime.combine(end_date, datetime.max.time()))

    if staff_id:
        query = query.filter(Appointment.staff_id == staff_id)

    if client_id:
        query = query.filter(Appointment.client_id == client_id)

    if status:
        query = query.filter(Appointment.status == AppointmentStatus(status))

    total = query.count()
    appointments = query.order_by(Appointment.start_time).offset(skip).limit(limit).all()

    items = [_appointment_to_response(a, db) for a in appointments]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/appointments/calendar")
async def get_calendar_view(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    salon_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    staff_id: Optional[int] = None,
):
    """
    Get appointments in calendar format for a date range.

    Returns appointments grouped by date for calendar display.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    query = db.query(Appointment).filter(
        Appointment.salon_id == salon_id,
        Appointment.start_time >= datetime.combine(start_date, datetime.min.time()),
        Appointment.start_time <= datetime.combine(end_date, datetime.max.time()),
        Appointment.status.notin_([AppointmentStatus.CANCELLED])
    )

    if staff_id:
        query = query.filter(Appointment.staff_id == staff_id)

    appointments = query.order_by(Appointment.start_time).all()

    # Group by date
    calendar = {}
    for appt in appointments:
        date_key = appt.start_time.date().isoformat()
        if date_key not in calendar:
            calendar[date_key] = []
        calendar[date_key].append(_appointment_to_response(appt, db))

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "dates": calendar,
        "total_appointments": len(appointments)
    }


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get appointment by ID."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    await require_salon_access(appointment.salon_id, current_user, db)

    return _appointment_to_response(appointment, db)


@router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appt_in: AppointmentUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update appointment details."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    await require_salon_access(appointment.salon_id, current_user, db)

    # Update fields
    update_data = appt_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(appointment, field) and field != "services":
            setattr(appointment, field, value)

    appointment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)

    return _appointment_to_response(appointment, db)


# ============================================================================
# Status Updates
# ============================================================================

@router.put("/appointments/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentStatusUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update appointment status."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    await require_salon_access(appointment.salon_id, current_user, db)

    new_status = AppointmentStatus(status_update.status)
    appointment.status = new_status

    # Handle specific status transitions
    if new_status == AppointmentStatus.CHECKED_IN:
        appointment.checked_in_at = datetime.utcnow()
    elif new_status == AppointmentStatus.IN_PROGRESS:
        appointment.started_at = datetime.utcnow()
    elif new_status == AppointmentStatus.COMPLETED:
        appointment.completed_at = datetime.utcnow()
    elif new_status == AppointmentStatus.CANCELLED:
        appointment.cancelled_at = datetime.utcnow()
        appointment.cancellation_reason = status_update.cancellation_reason
        if status_update.cancellation_fee:
            appointment.cancellation_fee = status_update.cancellation_fee
    elif new_status == AppointmentStatus.NO_SHOW:
        appointment.cancelled_at = datetime.utcnow()
        # Update client no-show count
        if appointment.client:
            appointment.client.no_show_count += 1

    if status_update.notes:
        appointment.staff_notes = status_update.notes

    appointment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)

    return _appointment_to_response(appointment, db)


@router.post("/appointments/{appointment_id}/check-in", response_model=AppointmentResponse)
async def check_in_appointment(
    appointment_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Check in a client for their appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    await require_salon_access(appointment.salon_id, current_user, db)

    if appointment.status != AppointmentStatus.SCHEDULED and appointment.status != AppointmentStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check in appointment with status: {appointment.status.value}"
        )

    appointment.status = AppointmentStatus.CHECKED_IN
    appointment.checked_in_at = datetime.utcnow()
    appointment.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(appointment)

    return _appointment_to_response(appointment, db)


@router.post("/appointments/{appointment_id}/start", response_model=AppointmentResponse)
async def start_appointment(
    appointment_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Start service for an appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    await require_salon_access(appointment.salon_id, current_user, db)

    appointment.status = AppointmentStatus.IN_PROGRESS
    appointment.started_at = datetime.utcnow()
    appointment.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(appointment)

    return _appointment_to_response(appointment, db)


@router.post("/appointments/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: int,
    checkout: AppointmentCheckout,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Complete appointment and process checkout."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    await require_salon_access(appointment.salon_id, current_user, db)

    appointment.status = AppointmentStatus.COMPLETED
    appointment.completed_at = datetime.utcnow()
    appointment.final_total = checkout.final_total
    appointment.updated_at = datetime.utcnow()

    # Update client stats
    if appointment.client:
        appointment.client.visit_count += 1
        appointment.client.last_visit = datetime.utcnow()
        appointment.client.total_spent = float(appointment.client.total_spent or 0) + checkout.final_total

    db.commit()
    db.refresh(appointment)

    return {
        "message": "Appointment completed",
        "appointment": _appointment_to_response(appointment, db),
        "final_total": checkout.final_total
    }


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    reason: Optional[str] = None,
):
    """Cancel an appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    await require_salon_access(appointment.salon_id, current_user, db)

    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = datetime.utcnow()
    appointment.cancellation_reason = reason
    appointment.updated_at = datetime.utcnow()

    # Update client cancellation count
    if appointment.client:
        appointment.client.cancellation_count += 1

    db.commit()
    db.refresh(appointment)

    return _appointment_to_response(appointment, db)


# ============================================================================
# Availability
# ============================================================================

@router.post("/appointments/available-slots", response_model=AvailableSlotsResponse)
async def get_available_slots(
    request: AvailableSlotsRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get available appointment slots for a given date and services."""
    salon = await require_salon_access(request.salon_id, current_user, db)

    # Calculate total service duration
    total_duration = 0
    for service_id in request.service_ids:
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.salon_id == request.salon_id
        ).first()
        if service:
            total_duration += service.total_duration

    if total_duration == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid services specified"
        )

    # Get staff members to check
    staff_query = db.query(Staff).filter(
        Staff.salon_id == request.salon_id,
        Staff.status == "active",
        Staff.show_on_booking == True
    )

    if request.staff_id:
        staff_query = staff_query.filter(Staff.id == request.staff_id)

    staff_members = staff_query.all()

    slots = []
    check_date = request.date.date() if isinstance(request.date, datetime) else request.date

    for staff in staff_members:
        # Get staff schedule for this day
        day_name = check_date.strftime("%A").lower()
        schedule = staff.default_schedule or {}
        day_schedule = schedule.get(day_name, {})

        if not day_schedule or not day_schedule.get("is_working", True):
            continue

        start_str = day_schedule.get("start", "09:00")
        end_str = day_schedule.get("end", "17:00")

        work_start = datetime.combine(check_date, datetime.strptime(start_str, "%H:%M").time())
        work_end = datetime.combine(check_date, datetime.strptime(end_str, "%H:%M").time())

        # Get existing appointments
        existing = db.query(Appointment).filter(
            Appointment.staff_id == staff.id,
            Appointment.start_time >= work_start,
            Appointment.start_time < work_end,
            Appointment.status.notin_([AppointmentStatus.CANCELLED])
        ).order_by(Appointment.start_time).all()

        # Find available slots
        current_time = work_start
        slot_duration = timedelta(minutes=15)  # 15-minute increments

        while current_time + timedelta(minutes=total_duration) <= work_end:
            slot_end = current_time + timedelta(minutes=total_duration)

            # Check if slot conflicts with existing appointments
            is_available = True
            for appt in existing:
                if current_time < appt.end_time and slot_end > appt.start_time:
                    is_available = False
                    break

            if is_available:
                slots.append(AppointmentSlot(
                    start_time=current_time,
                    end_time=slot_end,
                    staff_id=staff.id,
                    staff_name=staff.full_name
                ))

            current_time += slot_duration

    return AvailableSlotsResponse(
        date=datetime.combine(check_date, datetime.min.time()),
        slots=slots
    )


# ============================================================================
# Today's View
# ============================================================================

@router.get("/salons/{salon_id}/appointments/today")
async def get_todays_appointments(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    staff_id: Optional[int] = None,
):
    """Get today's appointments with summary stats."""
    salon = await require_salon_access(salon_id, current_user, db)

    today = date.today()
    start_dt = datetime.combine(today, datetime.min.time())
    end_dt = datetime.combine(today, datetime.max.time())

    query = db.query(Appointment).filter(
        Appointment.salon_id == salon_id,
        Appointment.start_time >= start_dt,
        Appointment.start_time <= end_dt
    )

    if staff_id:
        query = query.filter(Appointment.staff_id == staff_id)

    appointments = query.order_by(Appointment.start_time).all()

    # Calculate stats
    total = len(appointments)
    completed = sum(1 for a in appointments if a.status == AppointmentStatus.COMPLETED)
    in_progress = sum(1 for a in appointments if a.status == AppointmentStatus.IN_PROGRESS)
    checked_in = sum(1 for a in appointments if a.status == AppointmentStatus.CHECKED_IN)
    scheduled = sum(1 for a in appointments if a.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
    cancelled = sum(1 for a in appointments if a.status == AppointmentStatus.CANCELLED)

    revenue = sum(float(a.final_total or 0) for a in appointments if a.status == AppointmentStatus.COMPLETED)

    return {
        "date": today.isoformat(),
        "appointments": [_appointment_to_response(a, db) for a in appointments],
        "stats": {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "checked_in": checked_in,
            "scheduled": scheduled,
            "cancelled": cancelled,
            "revenue": revenue
        }
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _appointment_to_response(appointment: Appointment, db: Session) -> AppointmentResponse:
    """Convert Appointment model to AppointmentResponse schema."""
    from app.schemas.appointment import AppointmentServiceResponse

    # Get services
    services = []
    for appt_svc in appointment.services:
        services.append(AppointmentServiceResponse(
            id=appt_svc.id,
            service_id=appt_svc.service_id,
            service_name=appt_svc.service.name if appt_svc.service else "Unknown",
            price=float(appt_svc.price) if appt_svc.price else 0,
            duration_mins=appt_svc.duration_mins,
            sequence=appt_svc.sequence
        ))

    return AppointmentResponse(
        id=appointment.id,
        salon_id=appointment.salon_id,
        client_id=appointment.client_id,
        staff_id=appointment.staff_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        duration_mins=appointment.duration_mins,
        status=appointment.status.value if appointment.status else "scheduled",
        source=appointment.source.value if appointment.source else "online",
        checked_in_at=appointment.checked_in_at,
        started_at=appointment.started_at,
        completed_at=appointment.completed_at,
        estimated_total=float(appointment.estimated_total) if appointment.estimated_total else None,
        final_total=float(appointment.final_total) if appointment.final_total else None,
        deposit_amount=float(appointment.deposit_amount) if appointment.deposit_amount else 0,
        deposit_paid=appointment.deposit_paid,
        client_notes=appointment.client_notes,
        staff_notes=appointment.staff_notes,
        confirmation_sent=appointment.confirmation_sent,
        reminder_sent=appointment.reminder_sent,
        cancelled_at=appointment.cancelled_at,
        cancellation_reason=appointment.cancellation_reason,
        is_recurring=appointment.is_recurring,
        color=appointment.color,
        services=services,
        client_name=appointment.client.full_name if appointment.client else None,
        staff_name=appointment.staff.full_name if appointment.staff else None,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
    )
