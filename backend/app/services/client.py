"""
Client service
"""

from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Client, Appointment
from app.schemas.client import ClientCreate, ClientUpdate, ClientSearch
from app.services.base import BaseService


class ClientService(BaseService[Client, ClientCreate, ClientUpdate]):
    """Service for client operations"""

    def __init__(self):
        super().__init__(Client)

    async def get_by_email(
        self,
        db: AsyncSession,
        salon_id: int,
        email: str
    ) -> Optional[Client]:
        """Get client by email within a salon"""
        query = select(Client).where(
            and_(
                Client.salon_id == salon_id,
                Client.email == email
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_phone(
        self,
        db: AsyncSession,
        salon_id: int,
        phone: str
    ) -> Optional[Client]:
        """Get client by phone within a salon"""
        query = select(Client).where(
            and_(
                Client.salon_id == salon_id,
                Client.phone == phone
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        search: ClientSearch,
        skip: int = 0,
        limit: int = 20
    ) -> List[Client]:
        """Search clients with various filters"""
        query = select(Client).where(
            and_(
                Client.salon_id == salon_id,
                Client.is_active == True
            )
        )

        # Text search on name, email, phone
        if search.query:
            search_term = f"%{search.query}%"
            query = query.where(
                or_(
                    Client.first_name.ilike(search_term),
                    Client.last_name.ilike(search_term),
                    Client.email.ilike(search_term),
                    Client.phone.ilike(search_term)
                )
            )

        if search.is_vip is not None:
            query = query.where(Client.is_vip == search.is_vip)

        if search.loyalty_tier:
            query = query.where(Client.loyalty_tier == search.loyalty_tier)

        if search.tags:
            for tag in search.tags:
                query = query.where(Client.tags.contains([tag]))

        if search.last_visit_after:
            query = query.where(Client.last_visit >= search.last_visit_after)

        if search.last_visit_before:
            query = query.where(Client.last_visit <= search.last_visit_before)

        query = query.order_by(Client.last_name, Client.first_name)
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_visit_stats(
        self,
        db: AsyncSession,
        *,
        client: Client,
        appointment_total: float
    ) -> Client:
        """Update client stats after a completed appointment"""
        client.visit_count += 1
        client.last_visit = datetime.utcnow()
        client.total_spent = float(client.total_spent or 0) + appointment_total

        # Recalculate average ticket
        if client.visit_count > 0:
            client.average_ticket = float(client.total_spent) / client.visit_count

        # Update loyalty tier based on total spent
        client.loyalty_tier = self._calculate_loyalty_tier(float(client.total_spent))

        db.add(client)
        await db.commit()
        await db.refresh(client)
        return client

    def _calculate_loyalty_tier(self, total_spent: float) -> str:
        """Calculate loyalty tier based on total spend"""
        if total_spent >= 5000:
            return "platinum"
        elif total_spent >= 2500:
            return "gold"
        elif total_spent >= 1000:
            return "silver"
        return "bronze"

    async def get_vip_clients(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        limit: int = 20
    ) -> List[Client]:
        """Get VIP clients for a salon"""
        query = select(Client).where(
            and_(
                Client.salon_id == salon_id,
                Client.is_active == True,
                Client.is_vip == True
            )
        ).order_by(Client.total_spent.desc()).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_clients_needing_rebooking(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        days_since_visit: int = 45,
        limit: int = 50
    ) -> List[Client]:
        """Get clients who haven't visited in a while and have no upcoming appointment"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_since_visit)

        query = select(Client).where(
            and_(
                Client.salon_id == salon_id,
                Client.is_active == True,
                Client.last_visit < cutoff_date,
                or_(
                    Client.next_appointment.is_(None),
                    Client.next_appointment < datetime.utcnow()
                )
            )
        ).order_by(Client.last_visit.desc()).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_birthdays_this_month(
        self,
        db: AsyncSession,
        salon_id: int
    ) -> List[Client]:
        """Get clients with birthdays this month"""
        current_month = datetime.utcnow().month

        query = select(Client).where(
            and_(
                Client.salon_id == salon_id,
                Client.is_active == True,
                func.extract('month', Client.birthday) == current_month
            )
        ).order_by(func.extract('day', Client.birthday))

        result = await db.execute(query)
        return list(result.scalars().all())


# Singleton instance
client_service = ClientService()
