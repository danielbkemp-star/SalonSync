"""
Clients API Routes for SalonSync
CRUD operations for clients within a salon
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.database import get_db
from app.models import User, Salon, Client, Staff, Appointment
from app.schemas.client import (
    ClientCreate, ClientUpdate, ClientResponse, ClientListResponse,
    ClientSearch, ClientHistory, ClientConsent
)
from app.schemas.base import MessageResponse, PaginatedResponse
from app.api.dependencies import (
    CurrentUser, require_salon_access, SalonAccess, require_staff_role
)

router = APIRouter()


# ============================================================================
# CRUD Operations
# ============================================================================

@router.post("/salons/{salon_id}/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    salon_id: int,
    client_in: ClientCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Create a new client in the salon.

    Requires staff role.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    # Check for duplicate email within salon
    if client_in.email:
        existing = db.query(Client).filter(
            Client.salon_id == salon_id,
            Client.email == client_in.email.lower()
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client with this email already exists in this salon"
            )

    # Generate referral code
    import secrets
    referral_code = secrets.token_urlsafe(8).upper()[:8]

    # Create client
    client = Client(
        salon_id=salon_id,
        first_name=client_in.first_name,
        last_name=client_in.last_name,
        email=client_in.email.lower() if client_in.email else None,
        phone=client_in.phone,
        phone_secondary=client_in.phone_secondary,
        address_line1=client_in.address_line1,
        address_line2=client_in.address_line2,
        city=client_in.city,
        state=client_in.state,
        zip_code=client_in.zip_code,
        instagram_handle=client_in.instagram_handle,
        tiktok_handle=client_in.tiktok_handle,
        preferred_staff_id=client_in.preferred_staff_id,
        communication_preference=client_in.communication_preference,
        special_notes=client_in.special_notes,
        birthday=client_in.birthday,
        source=client_in.source,
        referred_by_id=client_in.referred_by_id,
        referral_code=referral_code,
    )

    # Set hair profile if provided
    if client_in.hair_profile:
        hp = client_in.hair_profile
        client.hair_type = hp.hair_type
        client.hair_color = hp.hair_color
        client.current_hair_color = hp.current_hair_color
        client.hair_texture = hp.hair_texture
        client.hair_length = hp.hair_length
        client.hair_density = hp.hair_density
        client.hair_porosity = hp.hair_porosity
        client.hair_color_history = hp.hair_color_history
        client.scalp_conditions = hp.scalp_conditions
        client.allergies = hp.allergies

    # Set consent if provided
    if client_in.consent:
        c = client_in.consent
        client.photo_consent = c.photo_consent
        client.social_media_consent = c.social_media_consent
        client.website_consent = c.website_consent
        client.sms_consent = c.sms_consent
        client.marketing_opt_in = c.marketing_opt_in
        client.consent_updated_at = datetime.utcnow()

    db.add(client)
    db.commit()
    db.refresh(client)

    return _client_to_response(client)


@router.get("/salons/{salon_id}/clients", response_model=ClientListResponse)
async def list_clients(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_vip: Optional[bool] = None,
    is_active: Optional[bool] = True,
    tags: Optional[str] = None,
):
    """
    List all clients in a salon.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    query = db.query(Client).filter(Client.salon_id == salon_id)

    if is_active is not None:
        query = query.filter(Client.is_active == is_active)

    if is_vip is not None:
        query = query.filter(Client.is_vip == is_vip)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Client.first_name.ilike(search_term),
                Client.last_name.ilike(search_term),
                Client.email.ilike(search_term),
                Client.phone.ilike(search_term)
            )
        )

    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        for tag in tag_list:
            query = query.filter(Client.tags.contains([tag]))

    total = query.count()
    clients = query.order_by(Client.last_name, Client.first_name).offset(skip).limit(limit).all()

    items = [_client_to_response(c) for c in clients]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/clients/search")
async def search_clients(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=2, description="Search query"),
    salon_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=50),
):
    """
    Search clients by name, email, or phone.

    Quick search endpoint for typeahead/autocomplete.
    """
    query = db.query(Client).filter(Client.is_active == True)

    # If salon_id specified, limit to that salon
    if salon_id:
        await require_salon_access(salon_id, current_user, db)
        query = query.filter(Client.salon_id == salon_id)
    elif not current_user.is_superuser:
        # Get salons user has access to
        staff_salons = db.query(Staff.salon_id).filter(
            Staff.user_id == current_user.id
        ).subquery()
        query = query.filter(Client.salon_id.in_(staff_salons))

    # Search
    search_term = f"%{q}%"
    query = query.filter(
        or_(
            Client.first_name.ilike(search_term),
            Client.last_name.ilike(search_term),
            Client.email.ilike(search_term),
            Client.phone.ilike(search_term),
            func.concat(Client.first_name, ' ', Client.last_name).ilike(search_term)
        )
    )

    clients = query.order_by(Client.last_name, Client.first_name).limit(limit).all()

    return {
        "results": [
            {
                "id": c.id,
                "full_name": c.full_name,
                "email": c.email,
                "phone": c.phone,
                "salon_id": c.salon_id,
                "is_vip": c.is_vip,
            }
            for c in clients
        ],
        "count": len(clients)
    }


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get client by ID."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    await require_salon_access(client.salon_id, current_user, db)

    return _client_to_response(client)


@router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_in: ClientUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update client details."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    await require_salon_access(client.salon_id, current_user, db)

    # Update fields
    update_data = client_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(client, field):
            setattr(client, field, value)

    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)

    return _client_to_response(client)


@router.delete("/clients/{client_id}")
async def delete_client(
    client_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Soft delete a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    await SalonAccess(require_manager=True)(client.salon_id, current_user, db)

    client.is_active = False
    client.updated_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message="Client deactivated successfully")


# ============================================================================
# Consent Management
# ============================================================================

@router.post("/clients/{client_id}/consent", response_model=ClientResponse)
async def update_client_consent(
    client_id: int,
    consent: ClientConsent,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update client consent settings.

    Important for photo/social media usage compliance.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    await require_salon_access(client.salon_id, current_user, db)

    # Update consent fields
    client.photo_consent = consent.photo_consent
    client.social_media_consent = consent.social_media_consent
    client.website_consent = consent.website_consent
    client.sms_consent = consent.sms_consent
    client.marketing_opt_in = consent.marketing_opt_in
    client.consent_updated_at = datetime.utcnow()
    client.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(client)

    return _client_to_response(client)


@router.get("/clients/{client_id}/consent")
async def get_client_consent(
    client_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get client's current consent settings."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    await require_salon_access(client.salon_id, current_user, db)

    return {
        "client_id": client.id,
        "photo_consent": client.photo_consent,
        "social_media_consent": client.social_media_consent,
        "website_consent": client.website_consent,
        "sms_consent": client.sms_consent,
        "marketing_opt_in": client.marketing_opt_in,
        "consent_updated_at": client.consent_updated_at,
    }


# ============================================================================
# History & Stats
# ============================================================================

@router.get("/clients/{client_id}/history", response_model=ClientHistory)
async def get_client_history(
    client_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
):
    """Get client's service history."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    await require_salon_access(client.salon_id, current_user, db)

    # Get recent appointments
    appointments = db.query(Appointment).filter(
        Appointment.client_id == client_id
    ).order_by(Appointment.start_time.desc()).limit(limit).all()

    appointment_list = [
        {
            "id": a.id,
            "date": a.start_time.isoformat(),
            "status": a.status.value if a.status else None,
            "services": [],  # Would need to join appointment_services
            "total": float(a.final_total) if a.final_total else None,
            "staff_name": a.staff.full_name if a.staff else None,
        }
        for a in appointments
    ]

    # Calculate favorite services (simplified)
    favorite_services = []  # Would need aggregation query

    return ClientHistory(
        client_id=client_id,
        appointments=appointment_list,
        total_visits=client.visit_count,
        total_spent=float(client.total_spent) if client.total_spent else 0,
        favorite_services=favorite_services,
        favorite_staff=client.preferred_staff.full_name if client.preferred_staff else None,
        hair_color_history=client.hair_color_history or [],
    )


@router.post("/clients/{client_id}/add-note")
async def add_client_note(
    client_id: int,
    note: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Add a note to client's special notes."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    await require_salon_access(client.salon_id, current_user, db)

    # Append to existing notes
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    user_name = current_user.first_name or "Staff"
    new_note = f"[{timestamp} - {user_name}] {note}"

    if client.special_notes:
        client.special_notes = f"{client.special_notes}\n\n{new_note}"
    else:
        client.special_notes = new_note

    client.updated_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message="Note added successfully")


# ============================================================================
# Tags
# ============================================================================

@router.post("/clients/{client_id}/tags")
async def add_client_tags(
    client_id: int,
    tags: List[str],
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Add tags to a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    await require_salon_access(client.salon_id, current_user, db)

    current_tags = client.tags or []
    for tag in tags:
        if tag not in current_tags:
            current_tags.append(tag)

    client.tags = current_tags
    client.updated_at = datetime.utcnow()
    db.commit()

    return {"tags": client.tags}


@router.delete("/clients/{client_id}/tags/{tag}")
async def remove_client_tag(
    client_id: int,
    tag: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Remove a tag from a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )

    await require_salon_access(client.salon_id, current_user, db)

    current_tags = client.tags or []
    if tag in current_tags:
        current_tags.remove(tag)
        client.tags = current_tags
        client.updated_at = datetime.utcnow()
        db.commit()

    return {"tags": client.tags}


# ============================================================================
# Helper Functions
# ============================================================================

def _client_to_response(client: Client) -> ClientResponse:
    """Convert Client model to ClientResponse schema."""
    return ClientResponse(
        id=client.id,
        salon_id=client.salon_id,
        user_id=client.user_id,
        first_name=client.first_name,
        last_name=client.last_name,
        email=client.email,
        phone=client.phone,
        full_name=client.full_name,
        phone_secondary=client.phone_secondary,
        address_line1=client.address_line1,
        city=client.city,
        state=client.state,
        zip_code=client.zip_code,
        instagram_handle=client.instagram_handle,
        tiktok_handle=client.tiktok_handle,
        preferred_staff_id=client.preferred_staff_id,
        communication_preference=client.communication_preference,
        hair_type=client.hair_type,
        hair_color=client.hair_color,
        current_hair_color=client.current_hair_color,
        hair_texture=client.hair_texture,
        photo_consent=client.photo_consent,
        social_media_consent=client.social_media_consent,
        marketing_opt_in=client.marketing_opt_in,
        loyalty_points=client.loyalty_points,
        loyalty_tier=client.loyalty_tier,
        visit_count=client.visit_count,
        total_spent=float(client.total_spent) if client.total_spent else 0,
        last_visit=client.last_visit,
        next_appointment=client.next_appointment,
        is_active=client.is_active,
        is_vip=client.is_vip,
        tags=client.tags or [],
        birthday=client.birthday.date() if client.birthday else None,
        source=client.source,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )
