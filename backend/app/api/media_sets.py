"""
MediaSet API routes - The Formula Vault
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, MediaSet, Salon
from app.schemas.media_set import (
    MediaSetCreate, MediaSetUpdate, MediaSetResponse, MediaSetListResponse,
    MediaSetSearch, GenerateComparisonRequest, ColorFormula
)
from app.schemas.base import MessageResponse, PaginatedResponse
from app.services.media_set import media_set_service
from app.services.cloudinary import cloudinary_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/media-sets", tags=["Media Sets (Formula Vault)"])


@router.post("", response_model=MediaSetResponse, status_code=status.HTTP_201_CREATED)
async def create_media_set(
    media_set_in: MediaSetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new media set (without photo upload)"""
    media_set = await media_set_service.create(db, obj_in=media_set_in)
    return media_set


@router.post("/with-photos", response_model=MediaSetResponse, status_code=status.HTTP_201_CREATED)
async def create_media_set_with_photos(
    salon_id: int = Form(...),
    staff_id: int = Form(...),
    client_id: Optional[int] = Form(None),
    appointment_id: Optional[int] = Form(None),
    before_photo: UploadFile = File(...),
    after_photo: UploadFile = File(...),
    services_performed: Optional[str] = Form(None),  # JSON string
    techniques_used: Optional[str] = Form(None),  # JSON string
    color_formulas: Optional[str] = Form(None),  # JSON string
    client_photo_consent: bool = Form(False),
    client_social_consent: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a media set with before/after photo uploads"""
    import json

    # Parse JSON fields
    services = json.loads(services_performed) if services_performed else []
    techniques = json.loads(techniques_used) if techniques_used else []
    formulas = json.loads(color_formulas) if color_formulas else []

    # Read photo data
    before_data = await before_photo.read()
    after_data = await after_photo.read()

    media_set_in = MediaSetCreate(
        salon_id=salon_id,
        staff_id=staff_id,
        client_id=client_id,
        appointment_id=appointment_id,
        services_performed=services,
        techniques_used=techniques,
        color_formulas=formulas,
        client_photo_consent=client_photo_consent,
        client_social_consent=client_social_consent,
        service_date=datetime.utcnow()
    )

    media_set = await media_set_service.create_with_photos(
        db,
        obj_in=media_set_in,
        before_photo_data=before_data,
        after_photo_data=after_data
    )

    return media_set


@router.get("/{media_set_id}", response_model=MediaSetResponse)
async def get_media_set(
    media_set_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get media set by ID"""
    media_set = await media_set_service.get(db, media_set_id)
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )
    return media_set


@router.get("/salon/{salon_id}", response_model=List[MediaSetResponse])
async def list_media_sets(
    salon_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    staff_id: Optional[int] = None,
    client_id: Optional[int] = None,
    is_portfolio: Optional[bool] = None,
    has_before_after: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List media sets for a salon with filters"""
    search = MediaSetSearch(
        staff_id=staff_id,
        client_id=client_id,
        is_portfolio_piece=is_portfolio,
        has_before_after=has_before_after
    )

    media_sets = await media_set_service.search(
        db, salon_id,
        search=search,
        skip=skip,
        limit=limit
    )
    return media_sets


@router.get("/salon/{salon_id}/portfolio", response_model=List[MediaSetResponse])
async def get_portfolio(
    salon_id: int,
    staff_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio pieces for public display"""
    media_sets = await media_set_service.get_portfolio(
        db, salon_id,
        staff_id=staff_id,
        limit=limit
    )
    return media_sets


@router.get("/client/{client_id}/history", response_model=List[MediaSetResponse])
async def get_client_service_history(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get service history for a client (includes formulas)"""
    media_sets = await media_set_service.get_client_history(db, client_id)
    return media_sets


@router.get("/client/{client_id}/formulas")
async def get_client_formula_history(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get color formula history for a client"""
    formulas = await media_set_service.get_formula_history(db, client_id)
    return formulas


@router.patch("/{media_set_id}", response_model=MediaSetResponse)
async def update_media_set(
    media_set_id: int,
    media_set_in: MediaSetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update media set"""
    media_set = await media_set_service.get(db, media_set_id)
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    media_set = await media_set_service.update(
        db, db_obj=media_set, obj_in=media_set_in
    )
    return media_set


@router.post("/{media_set_id}/comparison", response_model=MediaSetResponse)
async def generate_comparison_photo(
    media_set_id: int,
    layout: str = Query("side_by_side", pattern="^(side_by_side|top_bottom)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a comparison (side-by-side) photo"""
    media_set = await media_set_service.get(db, media_set_id)
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    if not media_set.before_photo_url or not media_set.after_photo_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both before and after photos are required"
        )

    media_set = await media_set_service.generate_comparison(
        db, media_set=media_set, layout=layout
    )
    return media_set


@router.post("/{media_set_id}/generate-caption")
async def generate_ai_caption(
    media_set_id: int,
    tone: str = Query("professional", pattern="^(professional|casual|fun|luxurious)$"),
    include_hashtags: bool = Query(True),
    hashtag_count: int = Query(15, ge=5, le=30),
    custom_instructions: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI caption for a media set"""
    media_set = await media_set_service.get(db, media_set_id)
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    result = await media_set_service.generate_ai_caption(
        db,
        media_set=media_set,
        tone=tone,
        include_hashtags=include_hashtags,
        hashtag_count=hashtag_count,
        custom_instructions=custom_instructions
    )
    return result


@router.post("/{media_set_id}/upload-photo")
async def upload_additional_photo(
    media_set_id: int,
    photo: UploadFile = File(...),
    photo_type: str = Query("detail", pattern="^(process|detail|styling)$"),
    caption: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an additional photo to a media set"""
    media_set = await media_set_service.get(db, media_set_id)
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    if not cloudinary_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image upload service not configured"
        )

    photo_data = await photo.read()

    result = await cloudinary_service.upload_image(
        photo_data,
        folder=f"salonsync/salon_{media_set.salon_id}/staff_{media_set.staff_id}/additional",
        tags=[photo_type, f"media_set_{media_set_id}"]
    )

    # Add to additional_photos
    additional_photos = media_set.additional_photos or []
    additional_photos.append({
        "url": result['url'],
        "public_id": result['public_id'],
        "type": photo_type,
        "caption": caption
    })

    media_set.additional_photos = additional_photos
    db.add(media_set)
    await db.commit()
    await db.refresh(media_set)

    return {"message": "Photo uploaded", "photo": result}


@router.delete("/{media_set_id}", response_model=MessageResponse)
async def delete_media_set(
    media_set_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a media set and its photos"""
    media_set = await media_set_service.get(db, media_set_id)
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    await media_set_service.delete_with_photos(db, media_set=media_set)
    return MessageResponse(message="Media set deleted successfully")
