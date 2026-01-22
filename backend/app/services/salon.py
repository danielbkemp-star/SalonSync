"""
Salon service - Business logic for salon management
"""

from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify

from app.models import Salon, Staff, Client, Appointment, Service
from app.schemas.salon import SalonCreate, SalonUpdate, SalonSettings, SalonStats
from app.services.base import BaseService


class SalonService(BaseService[Salon, SalonCreate, SalonUpdate]):
    """Service for salon operations"""

    def __init__(self):
        super().__init__(Salon)

    async def get_by_slug(
        self,
        db: AsyncSession,
        slug: str
    ) -> Optional[Salon]:
        """Get salon by URL slug"""
        return await self.get_by_field(db, "slug", slug)

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: SalonCreate,
        owner_id: Optional[int] = None
    ) -> Salon:
        """Create a new salon with auto-generated slug"""
        data = obj_in.model_dump(exclude_unset=True)

        # Generate unique slug if not provided
        if not data.get('slug'):
            base_slug = slugify(data['name'])
            slug = base_slug
            counter = 1

            # Ensure slug is unique
            while await self.get_by_slug(db, slug):
                slug = f"{base_slug}-{counter}"
                counter += 1

            data['slug'] = slug

        if owner_id:
            data['owner_id'] = owner_id

        db_obj = Salon(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_settings(
        self,
        db: AsyncSession,
        *,
        salon: Salon,
        settings: SalonSettings
    ) -> Salon:
        """Update salon booking/business settings"""
        update_data = settings.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(salon, field):
                setattr(salon, field, value)

        db.add(salon)
        await db.commit()
        await db.refresh(salon)
        return salon

    async def get_stats(
        self,
        db: AsyncSession,
        salon_id: int
    ) -> SalonStats:
        """Get salon statistics"""
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Total clients
        client_count = await db.execute(
            select(func.count()).select_from(Client)
            .where(Client.salon_id == salon_id)
            .where(Client.is_active == True)
        )
        total_clients = client_count.scalar() or 0

        # Total staff
        staff_count = await db.execute(
            select(func.count()).select_from(Staff)
            .where(Staff.salon_id == salon_id)
            .where(Staff.status == "active")
        )
        total_staff = staff_count.scalar() or 0

        # Today's appointments
        today_appts = await db.execute(
            select(func.count()).select_from(Appointment)
            .where(Appointment.salon_id == salon_id)
            .where(func.date(Appointment.start_time) == today)
        )
        total_appointments_today = today_appts.scalar() or 0

        # Completed today
        completed_today = await db.execute(
            select(func.count()).select_from(Appointment)
            .where(Appointment.salon_id == salon_id)
            .where(func.date(Appointment.start_time) == today)
            .where(Appointment.status == "completed")
        )
        appointments_completed_today = completed_today.scalar() or 0

        # Revenue today
        revenue_today = await db.execute(
            select(func.coalesce(func.sum(Appointment.final_total), 0))
            .where(Appointment.salon_id == salon_id)
            .where(func.date(Appointment.completed_at) == today)
            .where(Appointment.status == "completed")
        )
        total_revenue_today = float(revenue_today.scalar() or 0)

        # Revenue this week
        revenue_week = await db.execute(
            select(func.coalesce(func.sum(Appointment.final_total), 0))
            .where(Appointment.salon_id == salon_id)
            .where(func.date(Appointment.completed_at) >= week_ago)
            .where(Appointment.status == "completed")
        )
        total_revenue_week = float(revenue_week.scalar() or 0)

        # Revenue this month
        revenue_month = await db.execute(
            select(func.coalesce(func.sum(Appointment.final_total), 0))
            .where(Appointment.salon_id == salon_id)
            .where(func.date(Appointment.completed_at) >= month_ago)
            .where(Appointment.status == "completed")
        )
        total_revenue_month = float(revenue_month.scalar() or 0)

        # New clients this month
        new_clients = await db.execute(
            select(func.count()).select_from(Client)
            .where(Client.salon_id == salon_id)
            .where(func.date(Client.created_at) >= month_ago)
        )
        new_clients_this_month = new_clients.scalar() or 0

        return SalonStats(
            total_clients=total_clients,
            total_staff=total_staff,
            total_appointments_today=total_appointments_today,
            total_revenue_today=total_revenue_today,
            total_revenue_week=total_revenue_week,
            total_revenue_month=total_revenue_month,
            appointments_completed_today=appointments_completed_today,
            new_clients_this_month=new_clients_this_month,
        )

    async def connect_instagram(
        self,
        db: AsyncSession,
        *,
        salon: Salon,
        access_token: str,
        user_id: str,
        expires_at: Optional[datetime] = None
    ) -> Salon:
        """Connect Instagram account to salon"""
        salon.instagram_access_token = access_token
        salon.instagram_user_id = user_id
        salon.instagram_token_expires_at = expires_at

        db.add(salon)
        await db.commit()
        await db.refresh(salon)
        return salon

    async def disconnect_instagram(
        self,
        db: AsyncSession,
        *,
        salon: Salon
    ) -> Salon:
        """Disconnect Instagram account"""
        salon.instagram_access_token = None
        salon.instagram_user_id = None
        salon.instagram_token_expires_at = None

        db.add(salon)
        await db.commit()
        await db.refresh(salon)
        return salon

    async def connect_stripe(
        self,
        db: AsyncSession,
        *,
        salon: Salon,
        account_id: str
    ) -> Salon:
        """Connect Stripe account to salon"""
        salon.stripe_account_id = account_id

        db.add(salon)
        await db.commit()
        await db.refresh(salon)
        return salon

    async def update_stripe_status(
        self,
        db: AsyncSession,
        *,
        salon: Salon,
        charges_enabled: bool,
        payouts_enabled: bool,
        onboarding_complete: bool
    ) -> Salon:
        """Update Stripe account status"""
        salon.stripe_charges_enabled = charges_enabled
        salon.stripe_payouts_enabled = payouts_enabled
        salon.stripe_onboarding_complete = onboarding_complete

        db.add(salon)
        await db.commit()
        await db.refresh(salon)
        return salon


# Singleton instance
salon_service = SalonService()
