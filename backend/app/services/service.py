"""
Service service (for salon services/treatments)
"""

from typing import Optional, List, Dict

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Service
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.services.base import BaseService


class ServiceService(BaseService[Service, ServiceCreate, ServiceUpdate]):
    """Service for managing salon services"""

    def __init__(self):
        super().__init__(Service)

    async def get_active_by_salon(
        self,
        db: AsyncSession,
        salon_id: int
    ) -> List[Service]:
        """Get all active services for a salon"""
        query = select(Service).where(
            and_(
                Service.salon_id == salon_id,
                Service.is_active == True
            )
        ).order_by(Service.category, Service.display_order, Service.name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_bookable_services(
        self,
        db: AsyncSession,
        salon_id: int
    ) -> List[Service]:
        """Get services available for online booking"""
        query = select(Service).where(
            and_(
                Service.salon_id == salon_id,
                Service.is_active == True,
                Service.is_online_bookable == True
            )
        ).order_by(Service.category, Service.display_order)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_category(
        self,
        db: AsyncSession,
        salon_id: int,
        category: str
    ) -> List[Service]:
        """Get services by category"""
        query = select(Service).where(
            and_(
                Service.salon_id == salon_id,
                Service.category == category,
                Service.is_active == True
            )
        ).order_by(Service.display_order, Service.name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_grouped_by_category(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        bookable_only: bool = False
    ) -> Dict[str, List[Service]]:
        """Get services grouped by category"""
        if bookable_only:
            services = await self.get_bookable_services(db, salon_id)
        else:
            services = await self.get_active_by_salon(db, salon_id)

        grouped: Dict[str, List[Service]] = {}
        for service in services:
            if service.category not in grouped:
                grouped[service.category] = []
            grouped[service.category].append(service)

        return grouped

    async def get_addons(
        self,
        db: AsyncSession,
        salon_id: int
    ) -> List[Service]:
        """Get add-on services"""
        query = select(Service).where(
            and_(
                Service.salon_id == salon_id,
                Service.is_active == True,
                Service.is_addon == True
            )
        ).order_by(Service.category, Service.name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def calculate_duration(
        self,
        db: AsyncSession,
        service_ids: List[int]
    ) -> int:
        """Calculate total duration for multiple services"""
        if not service_ids:
            return 0

        query = select(Service).where(Service.id.in_(service_ids))
        result = await db.execute(query)
        services = list(result.scalars().all())

        total_duration = 0
        for service in services:
            total_duration += service.total_duration

        return total_duration

    async def calculate_price(
        self,
        db: AsyncSession,
        service_ids: List[int]
    ) -> float:
        """Calculate total price for multiple services"""
        if not service_ids:
            return 0.0

        query = select(Service).where(Service.id.in_(service_ids))
        result = await db.execute(query)
        services = list(result.scalars().all())

        return sum(float(s.price) for s in services)


# Singleton instance
service_service = ServiceService()
