"""
SalonSync Public Booking API
Client-facing endpoints for online booking (no authentication required).
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.salon import Salon
from app.models.staff import Staff
from app.models.service import Service
from app.models.client import Client
from app.models.appointment import Appointment, AppointmentStatus, AppointmentSource, AppointmentService
from app.services import scheduling_service, notification_service

router = APIRouter()


# ==================== SCHEMAS ====================

class PublicSalonInfo(BaseModel):
    """Public salon information for booking page."""
    id: int
    name: str
    slug: str
    address_line1: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    logo_url: Optional[str]
    booking_lead_time_hours: int
    booking_window_days: int
    cancellation_policy_hours: int

    class Config:
        from_attributes = True


class PublicStaffInfo(BaseModel):
    """Public staff information for booking."""
    id: int
    first_name: str
    last_name: str
    title: Optional[str]
    bio: Optional[str]
    photo_url: Optional[str]
    specialties: List[str] = []

    class Config:
        from_attributes = True


class PublicServiceInfo(BaseModel):
    """Public service information for booking."""
    id: int
    name: str
    description: Optional[str]
    category: str
    duration_minutes: int
    price: float
    price_max: Optional[float]
    is_price_variable: bool

    class Config:
        from_attributes = True


class TimeSlot(BaseModel):
    """Available time slot."""
    time: str  # HH:MM format
    datetime: datetime
    available: bool = True


class AvailabilityResponse(BaseModel):
    """Response for availability check."""
    date: date
    staff_id: int
    staff_name: str
    slots: List[TimeSlot]


class BookingRequest(BaseModel):
    """Request to create a booking."""
    # Client info
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)

    # Appointment info
    service_id: int
    staff_id: int
    date: date
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # HH:MM format

    # Optional
    notes: Optional[str] = None
    sms_reminders: bool = True
    email_reminders: bool = True


class BookingResponse(BaseModel):
    """Response after successful booking."""
    appointment_id: int
    confirmation_code: str
    service_name: str
    staff_name: str
    date: date
    time: str
    duration_minutes: int
    total_price: float
    salon_name: str
    salon_address: str
    salon_phone: str
    message: str


class BookingLookupResponse(BaseModel):
    """Response for booking lookup."""
    appointment_id: int
    status: str
    service_name: str
    staff_name: str
    date: date
    time: str
    duration_minutes: int
    salon_name: str
    salon_address: str
    can_cancel: bool
    can_reschedule: bool


# ==================== ENDPOINTS ====================

@router.get("/book/{salon_slug}", response_model=PublicSalonInfo)
async def get_salon_for_booking(
    salon_slug: str,
    db: Session = Depends(get_db)
):
    """Get salon information for the booking page."""
    salon = db.query(Salon).filter(
        Salon.slug == salon_slug,
        Salon.is_active == True
    ).first()

    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    return salon


@router.get("/book/{salon_slug}/services", response_model=List[PublicServiceInfo])
async def get_bookable_services(
    salon_slug: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get services available for online booking."""
    salon = db.query(Salon).filter(Salon.slug == salon_slug, Salon.is_active == True).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    query = db.query(Service).filter(
        Service.salon_id == salon.id,
        Service.is_active == True,
        Service.is_online_bookable == True
    )

    if category:
        query = query.filter(Service.category == category)

    services = query.order_by(Service.display_order, Service.name).all()
    return services


@router.get("/book/{salon_slug}/staff", response_model=List[PublicStaffInfo])
async def get_bookable_staff(
    salon_slug: str,
    service_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get staff available for online booking, optionally filtered by service."""
    salon = db.query(Salon).filter(Salon.slug == salon_slug, Salon.is_active == True).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    query = db.query(Staff).filter(
        Staff.salon_id == salon.id,
        Staff.status == "active",
        Staff.show_on_booking == True
    )

    staff = query.order_by(Staff.display_order, Staff.first_name).all()

    # Filter by service if specified
    if service_id:
        staff = [s for s in staff if service_id in (s.services or [])]

    return staff


@router.get("/book/{salon_slug}/availability", response_model=List[AvailabilityResponse])
async def get_availability(
    salon_slug: str,
    service_id: int,
    staff_id: Optional[int] = None,
    start_date: date = Query(default=None),
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get available time slots for a service."""
    salon = db.query(Salon).filter(Salon.slug == salon_slug, Salon.is_active == True).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    service = db.query(Service).filter(
        Service.id == service_id,
        Service.salon_id == salon.id,
        Service.is_active == True
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Default start date is today + lead time
    if not start_date:
        lead_time_hours = salon.booking_lead_time_hours or 2
        start_date = (datetime.now() + timedelta(hours=lead_time_hours)).date()

    # Enforce booking window
    max_date = datetime.now().date() + timedelta(days=salon.booking_window_days or 60)
    end_date = min(start_date + timedelta(days=days), max_date)

    # Get staff to check
    if staff_id:
        staff_list = db.query(Staff).filter(
            Staff.id == staff_id,
            Staff.salon_id == salon.id,
            Staff.status == "active"
        ).all()
    else:
        staff_list = db.query(Staff).filter(
            Staff.salon_id == salon.id,
            Staff.status == "active",
            Staff.show_on_booking == True
        ).all()
        # Filter to staff who can perform this service
        staff_list = [s for s in staff_list if service_id in (s.services or [])]

    results = []

    for staff in staff_list:
        current_date = start_date
        while current_date <= end_date:
            # Get available slots using scheduling service
            slots = scheduling_service.get_available_slots(
                db=db,
                salon_id=salon.id,
                staff_id=staff.id,
                date=current_date,
                duration_minutes=service.duration_minutes
            )

            if slots:
                results.append(AvailabilityResponse(
                    date=current_date,
                    staff_id=staff.id,
                    staff_name=f"{staff.first_name} {staff.last_name}",
                    slots=[
                        TimeSlot(
                            time=slot.strftime("%H:%M"),
                            datetime=datetime.combine(current_date, slot),
                            available=True
                        )
                        for slot in slots
                    ]
                ))

            current_date += timedelta(days=1)

    return results


@router.post("/book/{salon_slug}", response_model=BookingResponse)
async def create_booking(
    salon_slug: str,
    booking: BookingRequest,
    db: Session = Depends(get_db)
):
    """Create a new appointment booking."""
    # Get salon
    salon = db.query(Salon).filter(Salon.slug == salon_slug, Salon.is_active == True).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Get service
    service = db.query(Service).filter(
        Service.id == booking.service_id,
        Service.salon_id == salon.id,
        Service.is_active == True,
        Service.is_online_bookable == True
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found or not available for online booking")

    # Get staff
    staff = db.query(Staff).filter(
        Staff.id == booking.staff_id,
        Staff.salon_id == salon.id,
        Staff.status == "active"
    ).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    # Parse datetime
    try:
        hour, minute = map(int, booking.time.split(":"))
        appointment_datetime = datetime.combine(booking.date, datetime.min.time().replace(hour=hour, minute=minute))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format")

    # Validate booking time is in the future
    lead_time = timedelta(hours=salon.booking_lead_time_hours or 2)
    if appointment_datetime < datetime.now() + lead_time:
        raise HTTPException(
            status_code=400,
            detail=f"Appointments must be booked at least {salon.booking_lead_time_hours} hours in advance"
        )

    # Check availability
    is_available = scheduling_service.check_slot_available(
        db=db,
        salon_id=salon.id,
        staff_id=staff.id,
        start_time=appointment_datetime,
        duration_minutes=service.duration_minutes
    )
    if not is_available:
        raise HTTPException(status_code=409, detail="This time slot is no longer available")

    # Find or create client
    client = db.query(Client).filter(
        Client.salon_id == salon.id,
        Client.email == booking.email
    ).first()

    if not client:
        client = Client(
            salon_id=salon.id,
            first_name=booking.first_name,
            last_name=booking.last_name,
            email=booking.email,
            phone=booking.phone,
            source="online",
            sms_consent=booking.sms_reminders,
        )
        db.add(client)
        db.flush()
    else:
        # Update phone if different
        if booking.phone and client.phone != booking.phone:
            client.phone = booking.phone

    # Generate confirmation code
    import secrets
    confirmation_code = secrets.token_urlsafe(6).upper()[:8]

    # Create appointment
    end_time = appointment_datetime + timedelta(minutes=service.duration_minutes)

    appointment = Appointment(
        salon_id=salon.id,
        client_id=client.id,
        staff_id=staff.id,
        start_time=appointment_datetime,
        end_time=end_time,
        duration_mins=service.duration_minutes,
        status=AppointmentStatus.SCHEDULED,
        source=AppointmentSource.ONLINE,
        estimated_total=service.price,
        client_notes=booking.notes,
        confirmation_code=confirmation_code,
    )
    db.add(appointment)

    # Link service to appointment
    apt_service = AppointmentService(
        appointment=appointment,
        service_id=service.id,
        price=service.price,
        duration_mins=service.duration_minutes,
    )
    db.add(apt_service)

    db.commit()
    db.refresh(appointment)

    # Build salon address
    salon_address_parts = [salon.address_line1]
    if salon.city:
        salon_address_parts.append(f"{salon.city}, {salon.state or ''} {salon.zip_code or ''}".strip())
    salon_address = ", ".join(filter(None, salon_address_parts))

    # Send confirmation notifications
    notification_service.send_appointment_confirmation(
        client_email=client.email,
        client_phone=client.phone if booking.sms_reminders else None,
        client_name=f"{client.first_name} {client.last_name}",
        salon_name=salon.name,
        service_name=service.name,
        stylist_name=f"{staff.first_name} {staff.last_name}",
        appointment_date=appointment_datetime,
        duration_minutes=service.duration_minutes,
        salon_address=salon_address,
        salon_phone=salon.phone or "",
        send_email=booking.email_reminders,
        send_sms=booking.sms_reminders
    )

    return BookingResponse(
        appointment_id=appointment.id,
        confirmation_code=confirmation_code,
        service_name=service.name,
        staff_name=f"{staff.first_name} {staff.last_name}",
        date=booking.date,
        time=booking.time,
        duration_minutes=service.duration_minutes,
        total_price=service.price,
        salon_name=salon.name,
        salon_address=salon_address,
        salon_phone=salon.phone or "",
        message="Your appointment has been booked! A confirmation has been sent to your email."
    )


@router.get("/book/{salon_slug}/lookup")
async def lookup_booking(
    salon_slug: str,
    email: EmailStr = Query(...),
    confirmation_code: str = Query(...),
    db: Session = Depends(get_db)
):
    """Look up an existing booking by email and confirmation code."""
    salon = db.query(Salon).filter(Salon.slug == salon_slug).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Find client
    client = db.query(Client).filter(
        Client.salon_id == salon.id,
        Client.email == email
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Find appointment
    appointment = db.query(Appointment).filter(
        Appointment.salon_id == salon.id,
        Appointment.client_id == client.id,
        Appointment.confirmation_code == confirmation_code.upper()
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Get service name
    service_name = "Service"
    if appointment.services:
        service_name = appointment.services[0].service.name

    # Get staff name
    staff = db.query(Staff).filter(Staff.id == appointment.staff_id).first()
    staff_name = f"{staff.first_name} {staff.last_name}" if staff else "Staff"

    # Check if can cancel/reschedule
    cancellation_deadline = appointment.start_time - timedelta(hours=salon.cancellation_policy_hours or 24)
    can_modify = datetime.now() < cancellation_deadline and appointment.status in [
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.CONFIRMED
    ]

    salon_address_parts = [salon.address_line1]
    if salon.city:
        salon_address_parts.append(f"{salon.city}, {salon.state or ''} {salon.zip_code or ''}".strip())
    salon_address = ", ".join(filter(None, salon_address_parts))

    return BookingLookupResponse(
        appointment_id=appointment.id,
        status=appointment.status.value,
        service_name=service_name,
        staff_name=staff_name,
        date=appointment.start_time.date(),
        time=appointment.start_time.strftime("%H:%M"),
        duration_minutes=int((appointment.end_time - appointment.start_time).total_seconds() / 60),
        salon_name=salon.name,
        salon_address=salon_address,
        can_cancel=can_modify,
        can_reschedule=can_modify
    )


@router.post("/book/{salon_slug}/cancel")
async def cancel_booking(
    salon_slug: str,
    email: EmailStr = Query(...),
    confirmation_code: str = Query(...),
    db: Session = Depends(get_db)
):
    """Cancel an existing booking."""
    salon = db.query(Salon).filter(Salon.slug == salon_slug).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    client = db.query(Client).filter(
        Client.salon_id == salon.id,
        Client.email == email
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Booking not found")

    appointment = db.query(Appointment).filter(
        Appointment.salon_id == salon.id,
        Appointment.client_id == client.id,
        Appointment.confirmation_code == confirmation_code.upper()
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check if can cancel
    if appointment.status not in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]:
        raise HTTPException(status_code=400, detail="This appointment cannot be cancelled")

    cancellation_deadline = appointment.start_time - timedelta(hours=salon.cancellation_policy_hours or 24)
    if datetime.now() >= cancellation_deadline:
        raise HTTPException(
            status_code=400,
            detail=f"Appointments must be cancelled at least {salon.cancellation_policy_hours} hours in advance"
        )

    # Cancel the appointment
    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = datetime.now()
    appointment.cancelled_by = "client"
    appointment.cancellation_reason = "Cancelled by client online"

    db.commit()

    # Get service name for notification
    service_name = "Service"
    if appointment.services:
        service_name = appointment.services[0].service.name

    # Send cancellation notification
    notification_service.send_appointment_cancelled(
        client_email=client.email,
        client_phone=client.phone,
        client_name=f"{client.first_name} {client.last_name}",
        salon_name=salon.name,
        service_name=service_name,
        appointment_date=appointment.start_time,
        cancelled_by="client"
    )

    return {"message": "Your appointment has been cancelled"}
