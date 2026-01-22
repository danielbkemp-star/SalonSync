"""
Scheduling Service - Appointment availability and booking
Handles time slot calculation, conflict checking, and reminders
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import (
    Appointment, Staff, Service, Client, Salon,
    AppointmentService as AppointmentServiceModel
)
from app.models.appointment import AppointmentStatus
from app.schemas.appointment import AppointmentCreate
from app.app_settings import settings

logger = logging.getLogger(__name__)


class SchedulingService:
    """
    Appointment scheduling service.
    Handles availability calculation, booking, and reminders.
    """

    def __init__(self):
        # Default slot interval in minutes
        self.slot_interval = 15
        # Default buffer between appointments in minutes
        self.default_buffer = 0

    async def get_availability(
        self,
        db: Session,
        stylist_id: int,
        target_date: date,
        duration: int,
        *,
        salon_id: Optional[int] = None,
        service_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available time slots for a stylist on a specific date.

        Args:
            db: Database session
            stylist_id: Staff/stylist ID
            target_date: Date to check
            duration: Required duration in minutes
            salon_id: Salon ID (for validation)
            service_ids: Service IDs to include buffer times

        Returns:
            List of available time slots
        """
        # Get stylist
        stylist = db.query(Staff).filter(Staff.id == stylist_id).first()
        if not stylist:
            raise ValueError("Stylist not found")

        if not stylist.is_active:
            return []  # Inactive stylists have no availability

        # Get working hours for the day
        day_name = target_date.strftime("%A").lower()
        schedule = stylist.default_schedule or {}
        day_schedule = schedule.get(day_name)

        if not day_schedule or not day_schedule.get("working"):
            return []  # Not working this day

        start_time_str = day_schedule.get("start", "09:00")
        end_time_str = day_schedule.get("end", "17:00")

        # Parse times
        work_start = datetime.strptime(start_time_str, "%H:%M").time()
        work_end = datetime.strptime(end_time_str, "%H:%M").time()

        # Get existing appointments for the day
        day_start = datetime.combine(target_date, time.min)
        day_end = datetime.combine(target_date, time.max)

        existing_appointments = db.query(Appointment).filter(
            and_(
                Appointment.staff_id == stylist_id,
                Appointment.start_time >= day_start,
                Appointment.start_time <= day_end,
                Appointment.status.notin_([
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.NO_SHOW
                ])
            )
        ).order_by(Appointment.start_time).all()

        # Calculate buffer time from services
        total_buffer = self.default_buffer
        if service_ids:
            for service_id in service_ids:
                service = db.query(Service).filter(Service.id == service_id).first()
                if service:
                    total_buffer += (service.buffer_before_mins or 0) + (service.buffer_after_mins or 0)

        # Generate available slots
        slots = []
        current_time = datetime.combine(target_date, work_start)
        end_datetime = datetime.combine(target_date, work_end)

        # Don't show past slots for today
        now = datetime.utcnow()
        if target_date == now.date():
            # Round up to next slot interval
            minutes_past = now.minute % self.slot_interval
            if minutes_past > 0:
                current_time = now.replace(
                    minute=(now.minute - minutes_past + self.slot_interval),
                    second=0,
                    microsecond=0
                )
            else:
                current_time = now.replace(second=0, microsecond=0)

            # Add minimum booking lead time (e.g., 30 minutes)
            current_time = max(current_time, now + timedelta(minutes=30))

        while current_time + timedelta(minutes=duration) <= end_datetime:
            slot_end = current_time + timedelta(minutes=duration + total_buffer)

            # Check for conflicts
            is_available = True
            for appt in existing_appointments:
                # Check if this slot overlaps with existing appointment
                if self._times_overlap(
                    current_time, slot_end,
                    appt.start_time, appt.end_time
                ):
                    is_available = False
                    break

            if is_available:
                slots.append({
                    "start_time": current_time.isoformat(),
                    "end_time": (current_time + timedelta(minutes=duration)).isoformat(),
                    "duration_mins": duration,
                    "stylist_id": stylist_id,
                    "stylist_name": f"{stylist.user.first_name} {stylist.user.last_name}" if stylist.user else str(stylist_id),
                    "is_available": True
                })

            # Move to next slot
            current_time += timedelta(minutes=self.slot_interval)

        return slots

    async def get_multi_stylist_availability(
        self,
        db: Session,
        salon_id: int,
        target_date: date,
        duration: int,
        *,
        service_ids: Optional[List[int]] = None
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Get availability for all stylists in a salon.

        Returns:
            Dict mapping stylist_id to their available slots
        """
        stylists = db.query(Staff).filter(
            and_(
                Staff.salon_id == salon_id,
                Staff.is_active == True
            )
        ).all()

        availability = {}
        for stylist in stylists:
            slots = await self.get_availability(
                db,
                stylist.id,
                target_date,
                duration,
                salon_id=salon_id,
                service_ids=service_ids
            )
            if slots:
                availability[stylist.id] = slots

        return availability

    async def get_next_available(
        self,
        db: Session,
        stylist_id: int,
        duration: int,
        *,
        max_days: int = 14
    ) -> Optional[Dict[str, Any]]:
        """
        Find the next available slot for a stylist.

        Args:
            db: Database session
            stylist_id: Staff ID
            duration: Required duration in minutes
            max_days: Maximum days to look ahead

        Returns:
            First available slot or None
        """
        today = datetime.utcnow().date()

        for day_offset in range(max_days):
            check_date = today + timedelta(days=day_offset)
            slots = await self.get_availability(db, stylist_id, check_date, duration)

            if slots:
                return slots[0]

        return None

    async def book(
        self,
        db: Session,
        data: AppointmentCreate,
        *,
        created_by_id: int
    ) -> Appointment:
        """
        Create an appointment with conflict checking.

        Args:
            db: Database session
            data: Appointment creation data
            created_by_id: User ID creating the appointment

        Returns:
            Created appointment

        Raises:
            ValueError: If there's a scheduling conflict
        """
        # Calculate total duration and price from services
        total_duration = 0
        total_price = 0.0
        service_items = []

        for svc in data.services:
            service = db.query(Service).filter(Service.id == svc.service_id).first()
            if not service:
                raise ValueError(f"Service {svc.service_id} not found")

            duration = svc.duration_mins or service.total_duration
            price = svc.price if svc.price is not None else float(service.price or 0)

            service_items.append({
                'service_id': svc.service_id,
                'price': price,
                'duration_mins': duration,
                'sequence': svc.sequence
            })

            total_duration += duration
            total_price += price

        end_time = data.start_time + timedelta(minutes=total_duration)

        # Check for conflicts
        conflicts = await self.check_conflicts(
            db,
            staff_id=data.staff_id,
            start_time=data.start_time,
            end_time=end_time
        )

        if conflicts:
            raise ValueError(
                f"Time slot conflicts with {len(conflicts)} existing appointment(s)"
            )

        # Create appointment
        appointment = Appointment(
            salon_id=data.salon_id,
            client_id=data.client_id,
            staff_id=data.staff_id,
            start_time=data.start_time,
            end_time=end_time,
            duration_mins=total_duration,
            estimated_total=total_price,
            status=AppointmentStatus.SCHEDULED,
            notes=data.notes,
            client_notes=data.client_notes,
            source=data.source or "staff",
            created_by_id=created_by_id
        )

        db.add(appointment)
        db.flush()  # Get ID

        # Create service associations
        for item in service_items:
            appt_service = AppointmentServiceModel(
                appointment_id=appointment.id,
                **item
            )
            db.add(appt_service)

        db.commit()
        db.refresh(appointment)

        logger.info(
            f"Booked appointment {appointment.id} for client {data.client_id} "
            f"with stylist {data.staff_id}"
        )

        return appointment

    async def reschedule(
        self,
        db: Session,
        appointment: Appointment,
        new_start_time: datetime,
        *,
        new_staff_id: Optional[int] = None,
        notify_client: bool = True
    ) -> Appointment:
        """
        Reschedule an existing appointment.

        Args:
            db: Database session
            appointment: Existing appointment
            new_start_time: New start time
            new_staff_id: Optional new stylist
            notify_client: Whether to send notification

        Returns:
            Updated appointment
        """
        staff_id = new_staff_id or appointment.staff_id
        new_end_time = new_start_time + timedelta(minutes=appointment.duration_mins)

        # Check for conflicts
        conflicts = await self.check_conflicts(
            db,
            staff_id=staff_id,
            start_time=new_start_time,
            end_time=new_end_time,
            exclude_appointment_id=appointment.id
        )

        if conflicts:
            raise ValueError(
                f"New time slot conflicts with {len(conflicts)} existing appointment(s)"
            )

        # Update appointment
        old_time = appointment.start_time
        appointment.start_time = new_start_time
        appointment.end_time = new_end_time

        if new_staff_id:
            appointment.staff_id = new_staff_id

        appointment.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(appointment)

        # Send notification if requested
        if notify_client and appointment.client_id:
            await self._send_reschedule_notification(
                db, appointment, old_time
            )

        logger.info(
            f"Rescheduled appointment {appointment.id} "
            f"from {old_time} to {new_start_time}"
        )

        return appointment

    async def check_conflicts(
        self,
        db: Session,
        *,
        staff_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_appointment_id: Optional[int] = None
    ) -> List[Appointment]:
        """
        Check for conflicting appointments.

        Returns:
            List of conflicting appointments
        """
        query = db.query(Appointment).filter(
            and_(
                Appointment.staff_id == staff_id,
                Appointment.status.notin_([
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.NO_SHOW
                ]),
                or_(
                    # New appointment starts during existing
                    and_(
                        Appointment.start_time <= start_time,
                        Appointment.end_time > start_time
                    ),
                    # New appointment ends during existing
                    and_(
                        Appointment.start_time < end_time,
                        Appointment.end_time >= end_time
                    ),
                    # New appointment completely contains existing
                    and_(
                        Appointment.start_time >= start_time,
                        Appointment.end_time <= end_time
                    )
                )
            )
        )

        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)

        return query.all()

    async def send_reminder(
        self,
        db: Session,
        appointment: Appointment,
        *,
        method: str = "email"
    ) -> bool:
        """
        Send appointment reminder to client.

        Args:
            db: Database session
            appointment: Appointment to remind about
            method: "email", "sms", or "both"

        Returns:
            True if sent successfully
        """
        if not appointment.client_id:
            logger.warning(f"Appointment {appointment.id} has no client")
            return False

        client = db.query(Client).filter(Client.id == appointment.client_id).first()
        if not client:
            return False

        salon = db.query(Salon).filter(Salon.id == appointment.salon_id).first()
        stylist = db.query(Staff).filter(Staff.id == appointment.staff_id).first()

        # Get services for the appointment
        services = db.query(AppointmentServiceModel).filter(
            AppointmentServiceModel.appointment_id == appointment.id
        ).all()

        service_names = []
        for appt_svc in services:
            service = db.query(Service).filter(Service.id == appt_svc.service_id).first()
            if service:
                service_names.append(service.name)

        # Build reminder content
        reminder_data = {
            "client_name": f"{client.first_name} {client.last_name}",
            "client_email": client.email,
            "client_phone": client.phone,
            "salon_name": salon.name if salon else "the salon",
            "stylist_name": f"{stylist.user.first_name}" if stylist and stylist.user else "your stylist",
            "date": appointment.start_time.strftime("%A, %B %d, %Y"),
            "time": appointment.start_time.strftime("%I:%M %p"),
            "services": ", ".join(service_names) or "your appointment",
            "appointment_id": appointment.id
        }

        # In production, this would call email/SMS services
        # For now, just log and mark as sent
        logger.info(
            f"Sending {method} reminder for appointment {appointment.id} "
            f"to {reminder_data['client_name']}"
        )

        # Mark reminder as sent
        appointment.reminder_sent = True
        appointment.reminder_sent_at = datetime.utcnow()
        db.commit()

        return True

    async def send_confirmation(
        self,
        db: Session,
        appointment: Appointment
    ) -> bool:
        """Send appointment confirmation to client."""
        # Similar to send_reminder but for initial confirmation
        appointment.confirmation_sent = True
        appointment.confirmation_sent_at = datetime.utcnow()
        db.commit()

        logger.info(f"Sent confirmation for appointment {appointment.id}")
        return True

    async def get_upcoming_reminders(
        self,
        db: Session,
        salon_id: int,
        *,
        hours_before: int = 24
    ) -> List[Appointment]:
        """
        Get appointments that need reminders sent.

        Args:
            db: Database session
            salon_id: Salon ID
            hours_before: Hours before appointment to send reminder

        Returns:
            List of appointments needing reminders
        """
        reminder_window_start = datetime.utcnow()
        reminder_window_end = datetime.utcnow() + timedelta(hours=hours_before)

        return db.query(Appointment).filter(
            and_(
                Appointment.salon_id == salon_id,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED
                ]),
                Appointment.reminder_sent == False,
                Appointment.start_time >= reminder_window_start,
                Appointment.start_time <= reminder_window_end
            )
        ).order_by(Appointment.start_time).all()

    async def _send_reschedule_notification(
        self,
        db: Session,
        appointment: Appointment,
        old_time: datetime
    ):
        """Send notification about rescheduled appointment."""
        # In production, this would send email/SMS
        logger.info(
            f"Appointment {appointment.id} rescheduled from {old_time} "
            f"to {appointment.start_time}"
        )

    def _times_overlap(
        self,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime
    ) -> bool:
        """Check if two time ranges overlap."""
        return start1 < end2 and end1 > start2


# Singleton instance
scheduling_service = SchedulingService()
