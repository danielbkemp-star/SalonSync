"""
Staff service
"""

from typing import Optional, List
from datetime import datetime, date, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Staff, Appointment, User
from app.schemas.staff import StaffCreate, StaffUpdate
from app.services.base import BaseService


class StaffService(BaseService[Staff, StaffCreate, StaffUpdate]):
    """Service for staff operations"""

    def __init__(self):
        super().__init__(Staff)

    async def get_by_user_id(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[Staff]:
        """Get staff by user ID"""
        return await self.get_by_field(db, "user_id", user_id)

    async def get_active_by_salon(
        self,
        db: AsyncSession,
        salon_id: int
    ) -> List[Staff]:
        """Get all active staff for a salon"""
        query = select(Staff).where(
            and_(
                Staff.salon_id == salon_id,
                Staff.status == "active"
            )
        ).order_by(Staff.display_order)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_bookable_staff(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        service_id: Optional[int] = None
    ) -> List[Staff]:
        """Get staff available for online booking"""
        query = select(Staff).where(
            and_(
                Staff.salon_id == salon_id,
                Staff.status == "active",
                Staff.show_on_booking == True
            )
        ).order_by(Staff.display_order)

        result = await db.execute(query)
        staff_list = list(result.scalars().all())

        # Filter by service capability if specified
        if service_id:
            staff_list = [
                s for s in staff_list
                if service_id in (s.service_ids or [])
            ]

        return staff_list

    async def get_availability(
        self,
        db: AsyncSession,
        staff_id: int,
        target_date: date,
        *,
        duration_mins: int = 30
    ) -> List[dict]:
        """Get available time slots for a staff member on a specific date"""
        staff = await self.get(db, staff_id)
        if not staff:
            return []

        # Get staff schedule for the day
        day_name = target_date.strftime("%A").lower()
        schedule = (staff.default_schedule or {}).get(day_name)

        if not schedule or not schedule.get('is_working', True):
            return []

        start_time = datetime.strptime(schedule.get('start', '09:00'), '%H:%M')
        end_time = datetime.strptime(schedule.get('end', '17:00'), '%H:%M')

        # Get existing appointments for the day
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = datetime.combine(target_date, datetime.max.time())

        appointments_query = select(Appointment).where(
            and_(
                Appointment.staff_id == staff_id,
                Appointment.start_time >= day_start,
                Appointment.start_time <= day_end,
                Appointment.status.notin_(['cancelled', 'no_show'])
            )
        ).order_by(Appointment.start_time)

        result = await db.execute(appointments_query)
        appointments = list(result.scalars().all())

        # Generate available slots
        available_slots = []
        current_time = datetime.combine(target_date, start_time.time())
        end_datetime = datetime.combine(target_date, end_time.time())

        while current_time + timedelta(minutes=duration_mins) <= end_datetime:
            slot_end = current_time + timedelta(minutes=duration_mins)

            # Check if slot conflicts with any appointment
            is_available = True
            for appt in appointments:
                if not (slot_end <= appt.start_time or current_time >= appt.end_time):
                    is_available = False
                    break

            if is_available:
                available_slots.append({
                    "start": current_time.strftime('%H:%M'),
                    "end": slot_end.strftime('%H:%M')
                })

            # Move to next slot (15 min increments typical)
            current_time += timedelta(minutes=15)

        return available_slots


# Singleton instance
staff_service = StaffService()
