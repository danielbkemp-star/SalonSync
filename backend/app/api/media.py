"""
Media API Routes for SalonSync
MediaSets (Formula Vault) - before/after photos, formulas, techniques
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import MediaSet, Client
from app.schemas.media_set import (
    MediaSetCreate, MediaSetUpdate, MediaSetResponse, MediaSetListResponse,
    MediaSetSearch, GenerateComparisonRequest, FormulaSearch, ColorFormula
)
from app.schemas.social_post import CaptionGenerate, CaptionGenerateResponse
from app.schemas.base import MessageResponse, PaginatedResponse
from app.api.dependencies import (
    CurrentUser, require_salon_access, SalonAccess, UserStaffProfile
)
from app.services.cloudinary import cloudinary_service
from app.services.ai_caption import ai_caption_service
from app.services.media_service import media_service
from app.services.content_service import content_service

router = APIRouter()


# ============================================================================
# CRUD Operations
# ============================================================================

@router.post("/salons/{salon_id}/media-sets", response_model=MediaSetResponse, status_code=status.HTTP_201_CREATED)
async def create_media_set(
    salon_id: int,
    media_set_in: MediaSetCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Create a new media set (formula vault entry).

    Associates photos with color formulas, products, and techniques.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    # Get staff profile
    from app.models import Staff
    staff = db.query(Staff).filter(
        Staff.user_id == current_user.id,
        Staff.salon_id == salon_id
    ).first()

    if not staff and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff profile required to create media sets"
        )

    staff_id = staff.id if staff else media_set_in.staff_id

    # If client_id provided, verify client consent
    if media_set_in.client_id:
        client = db.query(Client).filter(
            Client.id == media_set_in.client_id,
            Client.salon_id == salon_id
        ).first()

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        # Use client's consent settings unless overridden
        photo_consent = media_set_in.client_photo_consent or client.photo_consent
        social_consent = media_set_in.client_social_consent or client.social_media_consent
        website_consent = media_set_in.client_website_consent or client.website_consent
    else:
        photo_consent = media_set_in.client_photo_consent
        social_consent = media_set_in.client_social_consent
        website_consent = media_set_in.client_website_consent

    # Create media set
    media_set = MediaSet(
        salon_id=salon_id,
        staff_id=staff_id,
        client_id=media_set_in.client_id,
        appointment_id=media_set_in.appointment_id,
        title=media_set_in.title,
        description=media_set_in.description,
        before_photo_url=media_set_in.before_photo_url,
        before_photo_public_id=media_set_in.before_photo_public_id,
        after_photo_url=media_set_in.after_photo_url,
        after_photo_public_id=media_set_in.after_photo_public_id,
        additional_photos=media_set_in.additional_photos,
        services_performed=media_set_in.services_performed,
        color_formulas=[f.model_dump() for f in media_set_in.color_formulas] if media_set_in.color_formulas else [],
        products_used=[p.model_dump() for p in media_set_in.products_used] if media_set_in.products_used else [],
        techniques_used=media_set_in.techniques_used,
        total_processing_time=media_set_in.total_processing_time,
        total_service_time=media_set_in.total_service_time,
        starting_level=media_set_in.starting_level,
        target_level=media_set_in.target_level,
        achieved_level=media_set_in.achieved_level,
        hair_condition_before=media_set_in.hair_condition_before,
        hair_condition_after=media_set_in.hair_condition_after,
        porosity=media_set_in.porosity,
        tags=media_set_in.tags,
        client_photo_consent=photo_consent,
        client_social_consent=social_consent,
        client_website_consent=website_consent,
        consent_method=media_set_in.consent_method,
        is_portfolio_piece=media_set_in.is_portfolio_piece,
        is_private=media_set_in.is_private,
        stylist_notes=media_set_in.stylist_notes,
        recommendations=media_set_in.recommendations,
        maintenance_tips=media_set_in.maintenance_tips,
        service_date=media_set_in.service_date or datetime.utcnow(),
    )

    db.add(media_set)
    db.commit()
    db.refresh(media_set)

    return _media_set_to_response(media_set)


@router.get("/salons/{salon_id}/media-sets", response_model=MediaSetListResponse)
async def list_media_sets(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    staff_id: Optional[int] = None,
    client_id: Optional[int] = None,
    is_portfolio_piece: Optional[bool] = None,
    has_before_after: Optional[bool] = None,
    can_post_to_social: Optional[bool] = None,
    tags: Optional[str] = None,
):
    """List media sets in a salon."""
    salon = await require_salon_access(salon_id, current_user, db)

    query = db.query(MediaSet).filter(
        MediaSet.salon_id == salon_id,
        MediaSet.is_private == False
    )

    if staff_id:
        query = query.filter(MediaSet.staff_id == staff_id)

    if client_id:
        query = query.filter(MediaSet.client_id == client_id)

    if is_portfolio_piece is not None:
        query = query.filter(MediaSet.is_portfolio_piece == is_portfolio_piece)

    if has_before_after:
        query = query.filter(
            MediaSet.before_photo_url.isnot(None),
            MediaSet.after_photo_url.isnot(None)
        )

    if can_post_to_social:
        query = query.filter(MediaSet.client_social_consent == True)

    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        for tag in tag_list:
            query = query.filter(MediaSet.tags.contains([tag]))

    total = query.count()
    media_sets = query.order_by(MediaSet.created_at.desc()).offset(skip).limit(limit).all()

    items = [_media_set_to_response(ms) for ms in media_sets]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/media-sets/{media_set_id}", response_model=MediaSetResponse)
async def get_media_set(
    media_set_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get media set by ID."""
    media_set = db.query(MediaSet).filter(MediaSet.id == media_set_id).first()
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    await require_salon_access(media_set.salon_id, current_user, db)

    return _media_set_to_response(media_set)


@router.put("/media-sets/{media_set_id}", response_model=MediaSetResponse)
async def update_media_set(
    media_set_id: int,
    media_set_in: MediaSetUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update media set."""
    media_set = db.query(MediaSet).filter(MediaSet.id == media_set_id).first()
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    await require_salon_access(media_set.salon_id, current_user, db)

    # Check ownership - only creator or manager can edit
    from app.models import Staff
    staff = db.query(Staff).filter(
        Staff.user_id == current_user.id,
        Staff.salon_id == media_set.salon_id
    ).first()

    if staff and staff.id != media_set.staff_id:
        await SalonAccess(require_manager=True)(media_set.salon_id, current_user, db)

    # Update fields
    update_data = media_set_in.model_dump(exclude_unset=True)

    # Handle nested objects
    if 'color_formulas' in update_data and update_data['color_formulas'] is not None:
        update_data['color_formulas'] = [
            f.model_dump() if hasattr(f, 'model_dump') else f
            for f in update_data['color_formulas']
        ]
    if 'products_used' in update_data and update_data['products_used'] is not None:
        update_data['products_used'] = [
            p.model_dump() if hasattr(p, 'model_dump') else p
            for p in update_data['products_used']
        ]

    for field, value in update_data.items():
        if hasattr(media_set, field):
            setattr(media_set, field, value)

    media_set.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(media_set)

    return _media_set_to_response(media_set)


@router.delete("/media-sets/{media_set_id}")
async def delete_media_set(
    media_set_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete media set (soft delete)."""
    media_set = db.query(MediaSet).filter(MediaSet.id == media_set_id).first()
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    await SalonAccess(require_manager=True)(media_set.salon_id, current_user, db)

    media_set.is_private = True  # Soft delete by making private
    media_set.updated_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message="Media set deleted successfully")


# ============================================================================
# Photo Operations
# ============================================================================

@router.post("/media-sets/{media_set_id}/generate-comparison")
async def generate_comparison(
    media_set_id: int,
    request: GenerateComparisonRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Generate side-by-side comparison photo from before/after images.

    Uses Cloudinary to create the comparison image.
    """
    media_set = db.query(MediaSet).filter(MediaSet.id == media_set_id).first()
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    await require_salon_access(media_set.salon_id, current_user, db)

    if not media_set.before_photo_url or not media_set.after_photo_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both before and after photos required for comparison"
        )

    try:
        # Generate comparison using MediaService
        comparison_url = await media_service.create_comparison(
            media_set.before_photo_url,
            media_set.after_photo_url,
            salon_id=media_set.salon_id,
            media_set_id=media_set.id,
            layout=request.layout,
            add_labels=request.add_labels if hasattr(request, 'add_labels') else True
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate comparison image: {str(e)}"
        )

    # Update media set with comparison URL
    media_set.comparison_photo_url = comparison_url
    media_set.updated_at = datetime.utcnow()
    db.commit()

    # Also get platform-optimized versions
    platform_urls = await media_service.get_platform_variants(comparison_url)

    return {
        "comparison_url": comparison_url,
        "platform_variants": platform_urls
    }


@router.post("/media-sets/{media_set_id}/add-formula")
async def add_formula(
    media_set_id: int,
    formula: ColorFormula,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Add a color formula to the media set."""
    media_set = db.query(MediaSet).filter(MediaSet.id == media_set_id).first()
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    await require_salon_access(media_set.salon_id, current_user, db)

    formulas = media_set.color_formulas or []
    formulas.append(formula.model_dump())
    media_set.color_formulas = formulas
    media_set.updated_at = datetime.utcnow()
    db.commit()

    return {"formulas": media_set.color_formulas, "count": len(formulas)}


# ============================================================================
# AI Caption Generation
# ============================================================================

@router.post("/media-sets/{media_set_id}/generate-caption", response_model=CaptionGenerateResponse)
async def generate_caption(
    media_set_id: int,
    request: CaptionGenerate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Generate AI caption for social media post.

    Uses Claude AI to create professional captions based on the service details.
    """
    media_set = db.query(MediaSet).filter(MediaSet.id == media_set_id).first()
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    await require_salon_access(media_set.salon_id, current_user, db)

    # Get salon name for personalization
    from app.models import Salon, Staff
    salon = db.query(Salon).filter(Salon.id == media_set.salon_id).first()
    staff = db.query(Staff).filter(Staff.id == media_set.staff_id).first()

    salon_name = salon.name if salon else None
    stylist_name = None
    if staff and staff.user:
        stylist_name = f"{staff.user.first_name} {staff.user.last_name}"

    try:
        # Use the new ContentService with rich JSON output
        result = await content_service.generate_caption(
            media_set,
            style=request.tone or "professional",
            salon_name=salon_name,
            stylist_name=stylist_name,
            custom_instructions=request.custom_instructions,
            include_cta=request.include_call_to_action,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate caption: {str(e)}"
        )

    # Store generated caption
    media_set.ai_generated_caption = result.get("caption")
    media_set.suggested_hashtags = result.get("hashtags", [])
    media_set.updated_at = datetime.utcnow()
    db.commit()

    return CaptionGenerateResponse(
        caption=result.get("caption", ""),
        hashtags=result.get("hashtags", []),
        alt_captions=result.get("alt_captions", []),
        suggested_post_time=result.get("suggested_post_time"),
        confidence_score=result.get("confidence_score"),
    )


# ============================================================================
# Search & Discovery
# ============================================================================

@router.post("/salons/{salon_id}/media-sets/search")
async def search_media_sets(
    salon_id: int,
    search: MediaSetSearch,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Advanced search for media sets."""
    salon = await require_salon_access(salon_id, current_user, db)

    query = db.query(MediaSet).filter(
        MediaSet.salon_id == salon_id,
        MediaSet.is_private == False
    )

    if search.staff_id:
        query = query.filter(MediaSet.staff_id == search.staff_id)

    if search.client_id:
        query = query.filter(MediaSet.client_id == search.client_id)

    if search.tags:
        for tag in search.tags:
            query = query.filter(MediaSet.tags.contains([tag]))

    if search.techniques:
        for tech in search.techniques:
            query = query.filter(MediaSet.techniques_used.contains([tech]))

    if search.has_before_after:
        query = query.filter(
            MediaSet.before_photo_url.isnot(None),
            MediaSet.after_photo_url.isnot(None)
        )

    if search.is_portfolio_piece is not None:
        query = query.filter(MediaSet.is_portfolio_piece == search.is_portfolio_piece)

    if search.can_post_to_social:
        query = query.filter(MediaSet.client_social_consent == True)

    if search.date_from:
        query = query.filter(MediaSet.service_date >= search.date_from)

    if search.date_to:
        query = query.filter(MediaSet.service_date <= search.date_to)

    total = query.count()
    media_sets = query.order_by(MediaSet.created_at.desc()).offset(skip).limit(limit).all()

    items = [_media_set_to_response(ms) for ms in media_sets]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.post("/salons/{salon_id}/formulas/search")
async def search_formulas(
    salon_id: int,
    search: FormulaSearch,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Search for color formulas across media sets.

    Useful for finding previous formulas used on similar hair.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    # Get all media sets with formulas
    query = db.query(MediaSet).filter(
        MediaSet.salon_id == salon_id,
        MediaSet.color_formulas.isnot(None)
    )

    if search.starting_level:
        query = query.filter(MediaSet.starting_level == search.starting_level)

    if search.target_level:
        query = query.filter(MediaSet.target_level == search.target_level)

    if search.technique:
        query = query.filter(MediaSet.techniques_used.contains([search.technique]))

    media_sets = query.order_by(MediaSet.created_at.desc()).limit(100).all()

    # Filter formulas by brand/color
    results = []
    for ms in media_sets:
        for formula in (ms.color_formulas or []):
            if search.brand and formula.get("brand", "").lower() != search.brand.lower():
                continue
            if search.color and search.color.lower() not in formula.get("color", "").lower():
                continue

            results.append({
                "media_set_id": ms.id,
                "service_date": ms.service_date.isoformat() if ms.service_date else None,
                "formula": formula,
                "starting_level": ms.starting_level,
                "achieved_level": ms.achieved_level,
                "techniques": ms.techniques_used,
                "staff_name": ms.staff.full_name if ms.staff else None,
            })

            if len(results) >= limit:
                break

        if len(results) >= limit:
            break

    return {"results": results, "count": len(results)}


# ============================================================================
# Helper Functions
# ============================================================================

def _media_set_to_response(media_set: MediaSet) -> MediaSetResponse:
    """Convert MediaSet model to MediaSetResponse schema."""
    from app.schemas.media_set import PhotoUpload, ColorFormula, ProductUsed

    # Determine computed fields
    has_before_after = bool(media_set.before_photo_url and media_set.after_photo_url)
    can_post = media_set.client_social_consent and has_before_after

    # Count photos
    photo_count = 0
    if media_set.before_photo_url:
        photo_count += 1
    if media_set.after_photo_url:
        photo_count += 1
    if media_set.additional_photos:
        photo_count += len(media_set.additional_photos)

    # Build formula summary
    formula_summary = ""
    if media_set.color_formulas:
        formulas = media_set.color_formulas[:2]  # First 2 formulas
        parts = [f"{f.get('brand', '')} {f.get('color', '')}" for f in formulas]
        formula_summary = " + ".join(parts)
        if len(media_set.color_formulas) > 2:
            formula_summary += f" (+{len(media_set.color_formulas) - 2} more)"

    return MediaSetResponse(
        id=media_set.id,
        salon_id=media_set.salon_id,
        staff_id=media_set.staff_id,
        client_id=media_set.client_id,
        appointment_id=media_set.appointment_id,
        title=media_set.title,
        description=media_set.description,
        before_photo_url=media_set.before_photo_url,
        after_photo_url=media_set.after_photo_url,
        comparison_photo_url=media_set.comparison_photo_url,
        additional_photos=[PhotoUpload(**p) if isinstance(p, dict) else p for p in (media_set.additional_photos or [])],
        services_performed=media_set.services_performed or [],
        color_formulas=[ColorFormula(**f) if isinstance(f, dict) else f for f in (media_set.color_formulas or [])],
        products_used=[ProductUsed(**p) if isinstance(p, dict) else p for p in (media_set.products_used or [])],
        techniques_used=media_set.techniques_used or [],
        total_processing_time=media_set.total_processing_time,
        total_service_time=media_set.total_service_time,
        starting_level=media_set.starting_level,
        target_level=media_set.target_level,
        achieved_level=media_set.achieved_level,
        hair_condition_before=media_set.hair_condition_before,
        hair_condition_after=media_set.hair_condition_after,
        tags=media_set.tags or [],
        ai_generated_caption=media_set.ai_generated_caption,
        suggested_hashtags=media_set.suggested_hashtags or [],
        client_photo_consent=media_set.client_photo_consent,
        client_social_consent=media_set.client_social_consent,
        client_website_consent=media_set.client_website_consent,
        is_portfolio_piece=media_set.is_portfolio_piece,
        is_featured=media_set.is_featured,
        is_private=media_set.is_private,
        photo_quality_rating=media_set.photo_quality_rating,
        stylist_notes=media_set.stylist_notes,
        recommendations=media_set.recommendations,
        maintenance_tips=media_set.maintenance_tips,
        client_satisfaction=media_set.client_satisfaction,
        client_feedback=media_set.client_feedback,
        service_date=media_set.service_date,
        has_before_after=has_before_after,
        can_post_to_social=can_post,
        photo_count=photo_count,
        formula_summary=formula_summary,
        staff_name=media_set.staff.full_name if media_set.staff else None,
        client_name=media_set.client.full_name if media_set.client else None,
        created_at=media_set.created_at,
        updated_at=media_set.updated_at,
    )
