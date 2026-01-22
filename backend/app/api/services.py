"""
Services API Routes for SalonSync
CRUD operations for services within a salon
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from app.database import get_db
from app.models import Service
from app.schemas.service import (
    ServiceCreate, ServiceUpdate, ServiceResponse, ServiceListResponse,
    ServicesByCategory
)
from app.schemas.base import MessageResponse, PaginatedResponse
from app.api.dependencies import (
    CurrentUser, require_salon_access, SalonAccess
)

router = APIRouter()


# ============================================================================
# CRUD Operations
# ============================================================================

@router.post("/salons/{salon_id}/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    salon_id: int,
    service_in: ServiceCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Create a new service in the salon.

    Requires manager role or higher.
    """
    salon = await SalonAccess(require_manager=True)(salon_id, current_user, db)

    service = Service(
        salon_id=salon_id,
        name=service_in.name,
        description=service_in.description,
        category=service_in.category,
        price=service_in.price,
        price_min=service_in.price_min,
        price_max=service_in.price_max,
        is_price_variable=service_in.is_price_variable,
        duration_mins=service_in.duration_mins,
        buffer_before_mins=service_in.buffer_before_mins,
        buffer_after_mins=service_in.buffer_after_mins,
        processing_time_mins=service_in.processing_time_mins,
        is_active=service_in.is_active,
        is_online_bookable=service_in.is_online_bookable,
        requires_consultation=service_in.requires_consultation,
        is_addon=service_in.is_addon,
        required_staff_count=service_in.required_staff_count,
        skill_level_required=service_in.skill_level_required,
        commission_type=service_in.commission_type,
        commission_value=service_in.commission_value,
        display_order=service_in.display_order,
        color=service_in.color,
        image_url=service_in.image_url,
        tags=service_in.tags,
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return _service_to_response(service)


@router.get("/salons/{salon_id}/services", response_model=ServiceListResponse)
async def list_services(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    is_online_bookable: Optional[bool] = None,
    is_addon: Optional[bool] = None,
):
    """
    List all services in a salon.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    query = db.query(Service).filter(Service.salon_id == salon_id)

    if is_active is not None:
        query = query.filter(Service.is_active == is_active)

    if category:
        query = query.filter(Service.category == category)

    if is_online_bookable is not None:
        query = query.filter(Service.is_online_bookable == is_online_bookable)

    if is_addon is not None:
        query = query.filter(Service.is_addon == is_addon)

    total = query.count()
    services = query.order_by(
        Service.category, Service.display_order, Service.name
    ).offset(skip).limit(limit).all()

    items = [_service_to_response(s) for s in services]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/salons/{salon_id}/services/by-category")
async def get_services_by_category(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    is_active: bool = True,
    is_online_bookable: Optional[bool] = None,
):
    """
    Get services grouped by category.

    Useful for booking UI where services are shown in categories.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    query = db.query(Service).filter(Service.salon_id == salon_id)

    if is_active:
        query = query.filter(Service.is_active == True)

    if is_online_bookable is not None:
        query = query.filter(Service.is_online_bookable == is_online_bookable)

    services = query.order_by(
        Service.category, Service.display_order, Service.name
    ).all()

    # Group by category
    categories_dict = {}
    for service in services:
        if service.category not in categories_dict:
            categories_dict[service.category] = []
        categories_dict[service.category].append(_service_to_response(service))

    return [
        {"category": cat, "services": svcs}
        for cat, svcs in categories_dict.items()
    ]


@router.get("/salons/{salon_id}/services/categories")
async def list_service_categories(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """Get list of all service categories in the salon."""
    salon = await require_salon_access(salon_id, current_user, db)

    categories = db.query(distinct(Service.category)).filter(
        Service.salon_id == salon_id,
        Service.is_active == True
    ).order_by(Service.category).all()

    return {"categories": [c[0] for c in categories if c[0]]}


@router.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get service by ID."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    await require_salon_access(service.salon_id, current_user, db)

    return _service_to_response(service)


@router.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_in: ServiceUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update service details.

    Requires manager role or higher.
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    await SalonAccess(require_manager=True)(service.salon_id, current_user, db)

    # Update fields
    update_data = service_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(service, field):
            setattr(service, field, value)

    service.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(service)

    return _service_to_response(service)


@router.delete("/services/{service_id}")
async def delete_service(
    service_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Deactivate a service.

    Requires manager role. Soft deletes by setting is_active=False.
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    await SalonAccess(require_manager=True)(service.salon_id, current_user, db)

    service.is_active = False
    service.updated_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message="Service deactivated successfully")


# ============================================================================
# Bulk Operations
# ============================================================================

@router.put("/salons/{salon_id}/services/reorder")
async def reorder_services(
    salon_id: int,
    service_orders: List[dict],  # [{"id": 1, "display_order": 0}, ...]
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Reorder services in bulk.

    Expects list of {"id": service_id, "display_order": order}
    """
    salon = await SalonAccess(require_manager=True)(salon_id, current_user, db)

    for item in service_orders:
        service = db.query(Service).filter(
            Service.id == item["id"],
            Service.salon_id == salon_id
        ).first()
        if service:
            service.display_order = item["display_order"]
            service.updated_at = datetime.utcnow()

    db.commit()

    return MessageResponse(message=f"Updated order for {len(service_orders)} services")


@router.post("/salons/{salon_id}/services/duplicate/{service_id}")
async def duplicate_service(
    salon_id: int,
    service_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Duplicate an existing service.

    Creates a copy with "(Copy)" appended to the name.
    """
    salon = await SalonAccess(require_manager=True)(salon_id, current_user, db)

    original = db.query(Service).filter(
        Service.id == service_id,
        Service.salon_id == salon_id
    ).first()

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    # Create copy
    new_service = Service(
        salon_id=salon_id,
        name=f"{original.name} (Copy)",
        description=original.description,
        category=original.category,
        price=original.price,
        price_min=original.price_min,
        price_max=original.price_max,
        is_price_variable=original.is_price_variable,
        duration_mins=original.duration_mins,
        buffer_before_mins=original.buffer_before_mins,
        buffer_after_mins=original.buffer_after_mins,
        processing_time_mins=original.processing_time_mins,
        is_active=False,  # Start as inactive
        is_online_bookable=original.is_online_bookable,
        requires_consultation=original.requires_consultation,
        is_addon=original.is_addon,
        required_staff_count=original.required_staff_count,
        skill_level_required=original.skill_level_required,
        commission_type=original.commission_type,
        commission_value=original.commission_value,
        display_order=original.display_order + 1,
        color=original.color,
        image_url=original.image_url,
        tags=original.tags,
    )

    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return _service_to_response(new_service)


# ============================================================================
# Helper Functions
# ============================================================================

def _service_to_response(service: Service) -> ServiceResponse:
    """Convert Service model to ServiceResponse schema."""
    return ServiceResponse(
        id=service.id,
        salon_id=service.salon_id,
        name=service.name,
        description=service.description,
        category=service.category,
        price=float(service.price) if service.price else 0,
        price_min=float(service.price_min) if service.price_min else None,
        price_max=float(service.price_max) if service.price_max else None,
        is_price_variable=service.is_price_variable,
        duration_mins=service.duration_mins,
        buffer_before_mins=service.buffer_before_mins or 0,
        buffer_after_mins=service.buffer_after_mins or 0,
        processing_time_mins=service.processing_time_mins or 0,
        total_duration=service.total_duration,
        is_active=service.is_active,
        is_online_bookable=service.is_online_bookable,
        requires_consultation=service.requires_consultation,
        is_addon=service.is_addon,
        required_staff_count=service.required_staff_count,
        skill_level_required=service.skill_level_required,
        commission_type=service.commission_type,
        commission_value=float(service.commission_value) if service.commission_value else None,
        display_order=service.display_order or 0,
        color=service.color,
        image_url=service.image_url,
        tags=service.tags or [],
        created_at=service.created_at,
        updated_at=service.updated_at,
    )
