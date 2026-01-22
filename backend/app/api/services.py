"""
Services API for SalonSync
"""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.models.service import Service

router = APIRouter()


class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    price: float
    duration_mins: int = 30
    is_online_bookable: bool = True
    is_addon: bool = False


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    duration_mins: Optional[int] = None
    buffer_before_mins: Optional[int] = None
    buffer_after_mins: Optional[int] = None
    is_active: Optional[bool] = None
    is_online_bookable: Optional[bool] = None
    is_addon: Optional[bool] = None
    display_order: Optional[int] = None
    color: Optional[str] = None


class ServiceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: str
    price: float
    price_min: Optional[float]
    price_max: Optional[float]
    duration_mins: int
    is_active: bool
    is_online_bookable: bool
    is_addon: bool
    color: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ServiceResponse])
async def list_services(
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    active_only: bool = True,
    online_bookable: Optional[bool] = None,
):
    """List all services."""
    query = db.query(Service)

    if active_only:
        query = query.filter(Service.is_active == True)

    if category:
        query = query.filter(Service.category == category)

    if online_bookable is not None:
        query = query.filter(Service.is_online_bookable == online_bookable)

    query = query.order_by(Service.category, Service.display_order, Service.name)
    return query.all()


@router.get("/categories")
async def list_categories(db: Session = Depends(get_db)):
    """List all service categories."""
    from sqlalchemy import distinct
    categories = db.query(distinct(Service.category)).filter(Service.is_active == True).all()
    return [c[0] for c in categories]


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific service."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    return service


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Create a new service (admin only)."""
    service = Service(
        name=service_data.name,
        description=service_data.description,
        category=service_data.category,
        price=service_data.price,
        duration_mins=service_data.duration_mins,
        is_online_bookable=service_data.is_online_bookable,
        is_addon=service_data.is_addon,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Update a service (admin only)."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    update_data = service_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Soft delete a service (admin only)."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    service.is_active = False
    db.commit()
