"""
Salon API routes
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Salon
from app.schemas.salon import (
    SalonCreate, SalonUpdate, SalonResponse, SalonListResponse,
    SalonSettings, SalonStats, SalonSocialConnect
)
from app.schemas.base import MessageResponse, PaginatedResponse
from app.services.salon import salon_service
from app.api.auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/salons", tags=["Salons"])


@router.post("", response_model=SalonResponse, status_code=status.HTTP_201_CREATED)
async def create_salon(
    salon_in: SalonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new salon"""
    salon = await salon_service.create(
        db,
        obj_in=salon_in,
        owner_id=current_user.id
    )
    return salon


@router.get("/{salon_id}", response_model=SalonResponse)
async def get_salon(
    salon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get salon by ID"""
    salon = await salon_service.get(db, salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )
    return salon


@router.get("/slug/{slug}", response_model=SalonResponse)
async def get_salon_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get salon by URL slug (public endpoint)"""
    salon = await salon_service.get_by_slug(db, slug)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )
    return salon


@router.patch("/{salon_id}", response_model=SalonResponse)
async def update_salon(
    salon_id: int,
    salon_in: SalonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update salon details"""
    salon = await salon_service.get(db, salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    salon = await salon_service.update(db, db_obj=salon, obj_in=salon_in)
    return salon


@router.patch("/{salon_id}/settings", response_model=SalonResponse)
async def update_salon_settings(
    salon_id: int,
    settings: SalonSettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update salon booking and business settings"""
    salon = await salon_service.get(db, salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    salon = await salon_service.update_settings(db, salon=salon, settings=settings)
    return salon


@router.get("/{salon_id}/stats", response_model=SalonStats)
async def get_salon_stats(
    salon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get salon statistics"""
    salon = await salon_service.get(db, salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    stats = await salon_service.get_stats(db, salon_id)
    return stats


# Social Media Connection Endpoints

@router.post("/{salon_id}/connect/instagram", response_model=SalonResponse)
async def connect_instagram(
    salon_id: int,
    connection: SalonSocialConnect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Connect Instagram account to salon.
    Requires OAuth code from Instagram authorization flow.
    """
    salon = await salon_service.get(db, salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    # TODO: Exchange auth_code for access_token via Instagram Graph API
    # This would involve calling Instagram's OAuth endpoint

    # For now, return error indicating implementation needed
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Instagram OAuth flow implementation required"
    )


@router.delete("/{salon_id}/connect/instagram", response_model=MessageResponse)
async def disconnect_instagram(
    salon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Disconnect Instagram account from salon"""
    salon = await salon_service.get(db, salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    await salon_service.disconnect_instagram(db, salon=salon)
    return MessageResponse(message="Instagram disconnected successfully")


@router.post("/{salon_id}/connect/stripe", response_model=SalonResponse)
async def connect_stripe(
    salon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Initialize Stripe Connect onboarding.
    Returns URL for Stripe onboarding flow.
    """
    salon = await salon_service.get(db, salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    # TODO: Create Stripe Connect account and return onboarding URL
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Stripe Connect implementation required"
    )


@router.delete("/{salon_id}", response_model=MessageResponse)
async def delete_salon(
    salon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Soft delete a salon (deactivate)"""
    salon = await salon_service.get(db, salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    await salon_service.soft_delete(db, id=salon_id)
    return MessageResponse(message="Salon deactivated successfully")
