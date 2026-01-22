"""
Clients API for SalonSync
"""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, require_staff
from app.database import get_db
from app.models.user import User
from app.models.client import Client

router = APIRouter()


class ClientCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    hair_type: Optional[str] = None
    hair_color: Optional[str] = None
    allergies: Optional[str] = None
    special_notes: Optional[str] = None
    preferred_staff_id: Optional[int] = None
    marketing_opt_in: Optional[bool] = None
    is_vip: Optional[bool] = None


class ClientResponse(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    is_active: bool
    is_vip: bool
    visit_count: int
    loyalty_points: int
    loyalty_tier: str
    total_spent: float

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    is_vip: Optional[bool] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
):
    """List all clients with optional filters."""
    query = db.query(Client).filter(Client.is_active == True)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Client.first_name.ilike(search_term)) |
            (Client.last_name.ilike(search_term)) |
            (Client.email.ilike(search_term)) |
            (Client.phone.ilike(search_term))
        )

    if is_vip is not None:
        query = query.filter(Client.is_vip == is_vip)

    query = query.order_by(Client.last_name, Client.first_name)
    return query.offset(offset).limit(limit).all()


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
):
    """Get a specific client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
):
    """Create a new client."""
    client = Client(
        first_name=client_data.first_name,
        last_name=client_data.last_name,
        email=client_data.email,
        phone=client_data.phone,
        special_notes=client_data.notes,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
):
    """Update a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    update_data = client_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
):
    """Soft delete a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    client.is_active = False
    db.commit()
