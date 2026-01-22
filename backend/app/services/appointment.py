"""
Appointment service
"""

from typing import Optional, List
from datetime import datetime, date, timedelta

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Appointment, AppointmentService as AppointmentServiceModel, Service, Client
from app.models.appointment import AppointmentStatus
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.base import BaseService


class AppointmentService(BaseService[Appointment, AppointmentCreate, AppointmentUpdate]):
    """Service for appointment operations"""

    def __init__(self):
        super().__init__(Appointment)

    async def create_appointment(
        self,
        db: AsyncSession,
        *,
        obj_in: AppointmentCreate
    ) -> Appointment:
        """Create appointment with services"""
        data = obj_in.model_dump(exclude={'services'})

        # Calculate end time based on services
        total_duration = 0
        service_items = []

        for svc in obj_in.services:
            # Get service details
            service = await db.get(Service, svc.service_id)
            if service:
                duration = svc.duration_mins or service.total_duration
                price = svc.price if svc.price is not None else float(service.price)

                service_items.append({
                    'service_id': svc.service_id,
                    'price': price,
                    'duration_mins': duration,
                    'sequence': svc.sequence
                })
                total_duration += duration

        data['duration_mins'] = total_duration
        data['end_time'] = data['start_time'] + timedelta(minutes=total_duration)
        data['estimated_total'] = sum(s['price'] for s in service_items)

        # Create appointment
        appointment = Appointment(**data)
        db.add(appointment)
        await db.flush()  # Get ID without committing

        # Create service associations
        for item in service_items:
            appt_service = AppointmentServiceModel(
                appointment_id=appointment.id,
                **item
            )
            db.add(appt_service)

        await db.commit()
        await db.refresh(appointment)
        return appointment

    async def get_by_date_range(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        start_date: datetime,
        end_date: datetime,
        staff_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Appointment]:
        """Get appointments within a date range"""
        query = select(Appointment).where(
            and_(
                Appointment.salon_id == salon_id,
                Appointment.start_time >= start_date,
                Appointment.start_time <= end_date
            )
        )

        if staff_id:
            query = query.where(Appointment.staff_id == staff_id)

        if status:
            query = query.where(Appointment.status == status)

        query = query.order_by(Appointment.start_time)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_todays_appointments(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        staff_id: Optional[int] = None
    ) -> List[Appointment]:
        """Get today's appointments"""
        today = datetime.utcnow().date()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())

        return await self.get_by_date_range(
            db, salon_id,
            start_date=start,
            end_date=end,
            staff_id=staff_id
        )

    async def update_status(
        self,
        db: AsyncSession,
        *,
        appointment: Appointment,
        status: str,
        notes: Optional[str] = None
    ) -> Appointment:
        """Update appointment status"""
        appointment.status = status

        if status == AppointmentStatus.CHECKED_IN:
            appointment.checked_in_at = datetime.utcnow()
        elif status == AppointmentStatus.IN_PROGRESS:
            appointment.started_at = datetime.utcnow()
        elif status == AppointmentStatus.COMPLETED:
            appointment.completed_at = datetime.utcnow()
        elif status == AppointmentStatus.CANCELLED:
            appointment.cancelled_at = datetime.utcnow()
            if notes:
                appointment.cancellation_reason = notes

        if notes and status != AppointmentStatus.CANCELLED:
            appointment.staff_notes = notes

        db.add(appointment)
        await db.commit()
        await db.refresh(appointment)
        return appointment

    async def reschedule(
        self,
        db: AsyncSession,
        *,
        appointment: Appointment,
        new_start_time: datetime,
        new_staff_id: Optional[int] = None
    ) -> Appointment:
        """Reschedule an appointment"""
        appointment.start_time = new_start_time
        appointment.end_time = new_start_time + timedelta(minutes=appointment.duration_mins)

        if new_staff_id:
            appointment.staff_id = new_staff_id

        db.add(appointment)
        await db.commit()
        await db.refresh(appointment)
        return appointment

    async def complete_checkout(
        self,
        db: AsyncSession,
        *,
        appointment: Appointment,
        final_total: float,
        payment_method: str,
        tip_amount: float = 0
    ) -> Appointment:
        """Complete appointment checkout"""
        appointment.status = AppointmentStatus.COMPLETED
        appointment.completed_at = datetime.utcnow()
        appointment.final_total = final_total
        appointment.payment_status = "paid"

        db.add(appointment)

        # Update client stats
        if appointment.client_id:
            from app.services.client import client_service
            client = await db.get(Client, appointment.client_id)
            if client:
                await client_service.update_visit_stats(
                    db,
                    client=client,
                    appointment_total=final_total
                )

        await db.commit()
        await db.refresh(appointment)
        return appointment

    async def check_conflicts(
        self,
        db: AsyncSession,
        *,
        staff_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_appointment_id: Optional[int] = None
    ) -> List[Appointment]:
        """Check for conflicting appointments"""
        query = select(Appointment).where(
            and_(
                Appointment.staff_id == staff_id,
                Appointment.status.notin_(['cancelled', 'no_show']),
                or_(
                    and_(
                        Appointment.start_time <= start_time,
                        Appointment.end_time > start_time
                    ),
                    and_(
                        Appointment.start_time < end_time,
                        Appointment.end_time >= end_time
                    ),
                    and_(
                        Appointment.start_time >= start_time,
                        Appointment.end_time <= end_time
                    )
                )
            )
        )

        if exclude_appointment_id:
            query = query.where(Appointment.id != exclude_appointment_id)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_upcoming_for_client(
        self,
        db: AsyncSession,
        client_id: int,
        *,
        limit: int = 5
    ) -> List[Appointment]:
        """Get upcoming appointments for a client"""
        query = select(Appointment).where(
            and_(
                Appointment.client_id == client_id,
                Appointment.start_time >= datetime.utcnow(),
                Appointment.status.notin_(['cancelled', 'no_show', 'completed'])
            )
        ).order_by(Appointment.start_time).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_needs_confirmation(
        self,
        db: AsyncSession,
        salon_id: int
    ) -> List[Appointment]:
        """Get appointments needing confirmation"""
        query = select(Appointment).where(
            and_(
                Appointment.salon_id == salon_id,
                Appointment.status == AppointmentStatus.SCHEDULED,
                Appointment.confirmation_sent == False,
                Appointment.start_time >= datetime.utcnow()
            )
        ).order_by(Appointment.start_time)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_needs_reminder(
        self,
        db: AsyncSession,
        salon_id: int,
        hours_before: int = 24
    ) -> List[Appointment]:
        """Get appointments needing reminder"""
        reminder_window_start = datetime.utcnow()
        reminder_window_end = datetime.utcnow() + timedelta(hours=hours_before)

        query = select(Appointment).where(
            and_(
                Appointment.salon_id == salon_id,
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
                Appointment.reminder_sent == False,
                Appointment.start_time >= reminder_window_start,
                Appointment.start_time <= reminder_window_end
            )
        ).order_by(Appointment.start_time)

        result = await db.execute(query)
        return list(result.scalars().all())


# Singleton instance
appointment_service = AppointmentService()
