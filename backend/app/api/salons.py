"""
Salon API Routes for SalonSync
Following RCMS patterns
"""

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Salon, Staff, Client, Appointment, Sale, Service
from app.models.appointment import AppointmentStatus
from app.models.user import UserRole
from app.schemas.salon import (
    SalonCreate, SalonUpdate, SalonResponse, SalonListResponse,
    SalonSettings, SalonStats, SalonSocialConnect, SalonSocialStatus,
    SalonPaymentStatus
)
from app.schemas.base import MessageResponse, PaginatedResponse
from app.api.dependencies import (
    CurrentUser, require_owner_role, require_manager_role,
    require_salon_access, require_salon_owner, SalonAccess
)

router = APIRouter()


# ============================================================================
# CRUD Operations
# ============================================================================

@router.post("", response_model=SalonResponse, status_code=status.HTTP_201_CREATED)
async def create_salon(
    salon_in: SalonCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Create a new salon.

    - User becomes the owner of the salon
    - Automatically creates a staff profile for the owner
    """
    # Generate slug if not provided
    if not salon_in.slug:
        from slugify import slugify
        base_slug = slugify(salon_in.name)
        slug = base_slug
        counter = 1
        while db.query(Salon).filter(Salon.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        salon_in.slug = slug
    else:
        # Check slug uniqueness
        if db.query(Salon).filter(Salon.slug == salon_in.slug).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Salon with this slug already exists"
            )

    # Create salon
    salon = Salon(
        name=salon_in.name,
        slug=salon_in.slug,
        description=salon_in.description,
        email=salon_in.email,
        phone=salon_in.phone,
        website=salon_in.website,
        address_line1=salon_in.address_line1,
        address_line2=salon_in.address_line2,
        city=salon_in.city,
        state=salon_in.state,
        zip_code=salon_in.zip_code,
        country=salon_in.country,
        timezone=salon_in.timezone,
        owner_id=current_user.id,
    )

    db.add(salon)
    db.flush()  # Get salon ID

    # Create staff profile for owner
    staff = Staff(
        salon_id=salon.id,
        user_id=current_user.id,
        title="Owner",
        status="active",
        show_on_booking=True,
    )
    db.add(staff)

    # Update user role to owner if they're a client
    if current_user.role == UserRole.CLIENT:
        current_user.role = UserRole.OWNER

    db.commit()
    db.refresh(salon)

    return salon


@router.get("", response_model=SalonListResponse)
async def list_salons(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
):
    """
    List salons the current user has access to.

    - Superusers see all salons
    - Regular users see salons where they have a staff profile
    """
    query = db.query(Salon)

    if not current_user.is_superuser:
        # Get salon IDs where user has staff profile
        staff_salon_ids = db.query(Staff.salon_id).filter(
            Staff.user_id == current_user.id
        ).subquery()
        query = query.filter(Salon.id.in_(staff_salon_ids))

    if search:
        query = query.filter(
            Salon.name.ilike(f"%{search}%") |
            Salon.city.ilike(f"%{search}%")
        )

    total = query.count()
    salons = query.order_by(Salon.name).offset(skip).limit(limit).all()

    return PaginatedResponse.create(
        items=salons,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/{salon_id}", response_model=SalonResponse)
async def get_salon(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get salon by ID."""
    salon = await require_salon_access(salon_id, current_user, db)
    return salon


@router.put("/{salon_id}", response_model=SalonResponse)
async def update_salon(
    salon_id: int,
    salon_in: SalonUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update salon details.

    Requires owner or manager role.
    """
    salon = await SalonAccess(require_manager=True)(salon_id, current_user, db)

    # Update fields
    update_data = salon_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(salon, field, value)

    salon.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(salon)

    return salon


@router.delete("/{salon_id}")
async def delete_salon(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) a salon.

    Requires owner role. Soft deletes by setting is_active=False.
    """
    salon = await SalonAccess(require_owner=True)(salon_id, current_user, db)

    salon.is_active = False
    salon.updated_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message="Salon deactivated successfully")


# ============================================================================
# Settings
# ============================================================================

@router.get("/{salon_id}/settings", response_model=SalonSettings)
async def get_salon_settings(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get salon booking and business settings."""
    salon = await require_salon_access(salon_id, current_user, db)

    return SalonSettings(
        booking_lead_time_hours=salon.booking_lead_time_hours,
        booking_window_days=salon.booking_window_days,
        cancellation_policy_hours=salon.cancellation_policy_hours,
        deposit_required=salon.deposit_required,
        deposit_percentage=float(salon.deposit_percentage) if salon.deposit_percentage else None,
        auto_confirm_appointments=salon.auto_confirm_appointments,
        send_confirmation_emails=salon.send_confirmation_emails,
        send_reminder_emails=salon.send_reminder_emails,
        reminder_hours_before=salon.reminder_hours_before,
    )


@router.put("/{salon_id}/settings", response_model=SalonSettings)
async def update_salon_settings(
    salon_id: int,
    settings: SalonSettings,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update salon booking and business settings."""
    salon = await SalonAccess(require_manager=True)(salon_id, current_user, db)

    update_data = settings.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(salon, field):
            setattr(salon, field, value)

    salon.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(salon)

    return settings


# ============================================================================
# Statistics
# ============================================================================

@router.get("/{salon_id}/stats", response_model=SalonStats)
async def get_salon_stats(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get salon statistics and metrics."""
    salon = await require_salon_access(salon_id, current_user, db)

    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Count clients
    total_clients = db.query(func.count(Client.id)).filter(
        Client.salon_id == salon_id,
        Client.is_active == True
    ).scalar() or 0

    # Count staff
    total_staff = db.query(func.count(Staff.id)).filter(
        Staff.salon_id == salon_id,
        Staff.status == "active"
    ).scalar() or 0

    # Today's appointments
    appointments_today = db.query(func.count(Appointment.id)).filter(
        Appointment.salon_id == salon_id,
        func.date(Appointment.start_time) == today
    ).scalar() or 0

    completed_today = db.query(func.count(Appointment.id)).filter(
        Appointment.salon_id == salon_id,
        func.date(Appointment.start_time) == today,
        Appointment.status == AppointmentStatus.COMPLETED
    ).scalar() or 0

    # Revenue calculations
    revenue_today = db.query(func.sum(Sale.total)).filter(
        Sale.salon_id == salon_id,
        func.date(Sale.created_at) == today,
        Sale.payment_status == "completed"
    ).scalar() or 0

    revenue_week = db.query(func.sum(Sale.total)).filter(
        Sale.salon_id == salon_id,
        func.date(Sale.created_at) >= week_ago,
        Sale.payment_status == "completed"
    ).scalar() or 0

    revenue_month = db.query(func.sum(Sale.total)).filter(
        Sale.salon_id == salon_id,
        func.date(Sale.created_at) >= month_ago,
        Sale.payment_status == "completed"
    ).scalar() or 0

    # New clients this month
    new_clients_month = db.query(func.count(Client.id)).filter(
        Client.salon_id == salon_id,
        func.date(Client.created_at) >= month_ago
    ).scalar() or 0

    return SalonStats(
        total_clients=total_clients,
        total_staff=total_staff,
        total_appointments_today=appointments_today,
        total_revenue_today=float(revenue_today),
        total_revenue_week=float(revenue_week),
        total_revenue_month=float(revenue_month),
        appointments_completed_today=completed_today,
        new_clients_this_month=new_clients_month,
    )


# ============================================================================
# Social Media Integration
# ============================================================================

@router.post("/{salon_id}/connect-instagram")
async def connect_instagram(
    salon_id: int,
    connect_data: SalonSocialConnect,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Connect Instagram Business account to salon.

    Requires owner role. Uses OAuth2 flow with Instagram Graph API.
    """
    salon = await SalonAccess(require_owner=True)(salon_id, current_user, db)

    if connect_data.platform != "instagram":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid platform. Use 'instagram' for this endpoint."
        )

    # TODO: Exchange auth_code for access token via Instagram API
    # For now, just store placeholder
    # In production:
    # 1. Exchange code for short-lived token
    # 2. Exchange short-lived for long-lived token
    # 3. Get connected Instagram Business Account ID

    # Placeholder - in production this would call Instagram API
    salon.instagram_access_token = f"placeholder_{connect_data.auth_code}"
    salon.instagram_token_expires_at = datetime.utcnow() + timedelta(days=60)
    salon.updated_at = datetime.utcnow()

    db.commit()

    return MessageResponse(message="Instagram connection initiated. Please complete OAuth flow.")


@router.post("/{salon_id}/connect-tiktok")
async def connect_tiktok(
    salon_id: int,
    connect_data: SalonSocialConnect,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Connect TikTok Business account to salon.

    Requires owner role. Uses OAuth2 flow with TikTok API.
    """
    salon = await SalonAccess(require_owner=True)(salon_id, current_user, db)

    if connect_data.platform != "tiktok":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid platform. Use 'tiktok' for this endpoint."
        )

    # TODO: Exchange auth_code for access token via TikTok API
    salon.tiktok_access_token = f"placeholder_{connect_data.auth_code}"
    salon.tiktok_token_expires_at = datetime.utcnow() + timedelta(days=60)
    salon.updated_at = datetime.utcnow()

    db.commit()

    return MessageResponse(message="TikTok connection initiated. Please complete OAuth flow.")


@router.get("/{salon_id}/social-status", response_model=SalonSocialStatus)
async def get_social_status(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get status of connected social media accounts."""
    salon = await require_salon_access(salon_id, current_user, db)

    return SalonSocialStatus(
        instagram_connected=bool(salon.instagram_access_token),
        instagram_handle=salon.instagram_handle,
        instagram_expires_at=salon.instagram_token_expires_at,
        tiktok_connected=bool(salon.tiktok_access_token),
        tiktok_handle=salon.tiktok_handle,
        tiktok_expires_at=salon.tiktok_token_expires_at,
        facebook_connected=False,  # Not implemented yet
    )


@router.delete("/{salon_id}/disconnect-instagram")
async def disconnect_instagram(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Disconnect Instagram account from salon."""
    salon = await SalonAccess(require_owner=True)(salon_id, current_user, db)

    salon.instagram_access_token = None
    salon.instagram_user_id = None
    salon.instagram_token_expires_at = None
    salon.updated_at = datetime.utcnow()

    db.commit()

    return MessageResponse(message="Instagram disconnected successfully")


# ============================================================================
# Stripe Payment Integration
# ============================================================================

@router.post("/{salon_id}/connect-stripe")
async def connect_stripe(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Initialize Stripe Connect onboarding.

    Returns a Stripe Connect onboarding URL for the salon owner.
    """
    salon = await SalonAccess(require_owner=True)(salon_id, current_user, db)

    # TODO: Create Stripe Connect account and return onboarding URL
    # For now, return placeholder
    # In production:
    # 1. Create Stripe Connect account
    # 2. Generate onboarding link
    # 3. Return URL for user to complete onboarding

    return {
        "message": "Stripe Connect integration",
        "onboarding_url": f"https://connect.stripe.com/setup/placeholder/{salon_id}",
        "note": "Complete Stripe onboarding to accept payments"
    }


@router.get("/{salon_id}/payment-status", response_model=SalonPaymentStatus)
async def get_payment_status(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get status of payment integrations."""
    salon = await require_salon_access(salon_id, current_user, db)

    return SalonPaymentStatus(
        stripe_connected=bool(salon.stripe_account_id),
        stripe_charges_enabled=salon.stripe_charges_enabled if hasattr(salon, 'stripe_charges_enabled') else False,
        stripe_payouts_enabled=salon.stripe_payouts_enabled if hasattr(salon, 'stripe_payouts_enabled') else False,
        square_connected=bool(salon.square_location_id) if hasattr(salon, 'square_location_id') else False,
    )
