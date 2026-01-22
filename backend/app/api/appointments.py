"""
Appointments API for SalonSync
"""

from datetime import datetime, date
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.api.auth import get_current_user, require_staff
from app.database import get_db
from app.models.user import User
from app.models.appointment import Appointment, AppointmentService, AppointmentStatus, AppointmentSource
from app.models.service import Service

router = APIRouter()


class AppointmentServiceCreate(BaseModel):
    service_id: int
    price: Optional[float] = None  # Override price if needed


class AppointmentCreate(BaseModel):
    client_id: int
    staff_id: int
    start_time: datetime
    services: List[AppointmentServiceCreate]
    client_notes: Optional[str] = None
    source: str = "online"


class AppointmentUpdate(BaseModel):
    staff_id: Optional[int] = None
    start_time: Optional[datetime] = None
    status: Optional[str] = None
    client_notes: Optional[str] = None
    staff_notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    client_id: int
    staff_id: int
    start_time: datetime
    end_time: datetime
    duration_mins: int
    status: str
    source: str
    estimated_total: Optional[float]
    client_notes: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AppointmentResponse])
async def list_appointments(
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    staff_id: Optional[int] = None,
    client_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """List appointments with filters."""
    query = db.query(Appointment).options(
        joinedload(Appointment.services).joinedload(AppointmentService.service)
    )

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

    query = query.order_by(Appointment.start_time)
    return query.all()


@router.get("/today", response_model=List[AppointmentResponse])
async def get_todays_appointments(
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
    staff_id: Optional[int] = None,
):
    """Get today's appointments."""
    today = date.today()
    return await list_appointments(
        current_user=current_user,
        db=db,
        start_date=today,
        end_date=today,
        staff_id=staff_id,
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Get a specific appointment."""
    appointment = db.query(Appointment).options(
        joinedload(Appointment.services).joinedload(AppointmentService.service)
    ).filter(Appointment.id == appointment_id).first()

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    return appointment


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appt_data: AppointmentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Book a new appointment."""
    # Calculate total duration and price
    total_duration = 0
    total_price = 0

    services_to_add = []
    for svc_data in appt_data.services:
        service = db.query(Service).filter(Service.id == svc_data.service_id).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Service {svc_data.service_id} not found"
            )
        price = svc_data.price if svc_data.price is not None else float(service.price)
        total_duration += service.total_duration
        total_price += price
        services_to_add.append((service, price))

    # Calculate end time
    from datetime import timedelta
    end_time = appt_data.start_time + timedelta(minutes=total_duration)

    # Create appointment
    appointment = Appointment(
        client_id=appt_data.client_id,
        staff_id=appt_data.staff_id,
        start_time=appt_data.start_time,
        end_time=end_time,
        duration_mins=total_duration,
        status=AppointmentStatus.SCHEDULED,
        source=AppointmentSource(appt_data.source),
        estimated_total=total_price,
        client_notes=appt_data.client_notes,
        created_by_id=current_user.id,
    )
    db.add(appointment)
    db.flush()

    # Add services
    for i, (service, price) in enumerate(services_to_add):
        appt_service = AppointmentService(
            appointment_id=appointment.id,
            service_id=service.id,
            price=price,
            duration_mins=service.duration_mins,
            sequence=i,
        )
        db.add(appt_service)

    db.commit()
    db.refresh(appointment)
    return appointment


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appt_data: AppointmentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Update an appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    update_data = appt_data.model_dump(exclude_unset=True)

    if "status" in update_data:
        update_data["status"] = AppointmentStatus(update_data["status"])

    for field, value in update_data.items():
        setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/{appointment_id}/check-in", response_model=AppointmentResponse)
async def check_in_appointment(
    appointment_id: int,
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
):
    """Check in a client for their appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    appointment.status = AppointmentStatus.CHECKED_IN
    appointment.checked_in_at = datetime.utcnow()
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    reason: Optional[str] = None,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Cancel an appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = datetime.utcnow()
    appointment.cancelled_by = "staff" if current_user.is_staff else "client"
    appointment.cancellation_reason = reason
    db.commit()
    db.refresh(appointment)
    return appointment
