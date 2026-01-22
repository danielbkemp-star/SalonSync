"""
MediaSet schemas - The Formula Vault
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class ColorFormula(BaseSchema):
    """Individual color formula"""
    zone: str = Field(..., description="Application zone: roots, mids, ends, all_over, highlights, lowlights, gloss, balayage")
    brand: str
    line: Optional[str] = None  # Product line, e.g., "Koleston Perfect"
    color: str  # Color code/name
    developer: Optional[str] = None  # Developer volume
    ratio: Optional[str] = None  # Mix ratio
    processing_time: Optional[str] = None
    heat: bool = False
    notes: Optional[str] = None


class ProductUsed(BaseSchema):
    """Product used during service"""
    name: str
    brand: Optional[str] = None
    amount: Optional[str] = None
    step: Optional[str] = None  # When in the process it was used


class PhotoUpload(BaseSchema):
    """Photo upload details"""
    url: str
    public_id: str
    caption: Optional[str] = None
    type: str = "detail"  # before, after, process, detail, styling


class MediaSetBase(BaseSchema):
    """Base media set fields"""
    title: Optional[str] = None
    description: Optional[str] = None


class MediaSetCreate(MediaSetBase):
    """Schema for creating a media set"""
    salon_id: int
    staff_id: int
    client_id: Optional[int] = None
    appointment_id: Optional[int] = None

    # Photos (Cloudinary URLs after upload)
    before_photo_url: Optional[str] = None
    before_photo_public_id: Optional[str] = None
    after_photo_url: Optional[str] = None
    after_photo_public_id: Optional[str] = None
    additional_photos: List[PhotoUpload] = []

    # Services
    services_performed: List[str] = []

    # THE FORMULA VAULT
    color_formulas: List[ColorFormula] = []
    products_used: List[ProductUsed] = []
    techniques_used: List[str] = []

    # Processing details
    total_processing_time: Optional[str] = None
    total_service_time: Optional[str] = None

    # Hair details
    starting_level: Optional[str] = None
    target_level: Optional[str] = None
    achieved_level: Optional[str] = None
    hair_condition_before: Optional[str] = None
    hair_condition_after: Optional[str] = None
    porosity: Optional[str] = None

    # Tags
    tags: List[str] = []

    # Consent
    client_photo_consent: bool = False
    client_social_consent: bool = False
    client_website_consent: bool = False
    consent_method: Optional[str] = None

    # Portfolio
    is_portfolio_piece: bool = False
    is_private: bool = False

    # Notes
    stylist_notes: Optional[str] = None
    recommendations: Optional[str] = None
    maintenance_tips: Optional[str] = None

    # Service date
    service_date: Optional[datetime] = None


class MediaSetUpdate(BaseSchema):
    """Schema for updating a media set"""
    title: Optional[str] = None
    description: Optional[str] = None

    # Photos
    before_photo_url: Optional[str] = None
    before_photo_public_id: Optional[str] = None
    after_photo_url: Optional[str] = None
    after_photo_public_id: Optional[str] = None
    comparison_photo_url: Optional[str] = None
    comparison_photo_public_id: Optional[str] = None
    additional_photos: Optional[List[PhotoUpload]] = None

    # Services
    services_performed: Optional[List[str]] = None

    # THE FORMULA VAULT
    color_formulas: Optional[List[ColorFormula]] = None
    products_used: Optional[List[ProductUsed]] = None
    techniques_used: Optional[List[str]] = None

    # Processing details
    total_processing_time: Optional[str] = None
    total_service_time: Optional[str] = None

    # Hair details
    starting_level: Optional[str] = None
    target_level: Optional[str] = None
    achieved_level: Optional[str] = None
    hair_condition_before: Optional[str] = None
    hair_condition_after: Optional[str] = None
    porosity: Optional[str] = None

    # Tags
    tags: Optional[List[str]] = None

    # Consent
    client_photo_consent: Optional[bool] = None
    client_social_consent: Optional[bool] = None
    client_website_consent: Optional[bool] = None

    # Portfolio
    is_portfolio_piece: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_private: Optional[bool] = None
    photo_quality_rating: Optional[int] = Field(None, ge=1, le=5)

    # Notes
    stylist_notes: Optional[str] = None
    recommendations: Optional[str] = None
    maintenance_tips: Optional[str] = None

    # Client feedback
    client_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    client_feedback: Optional[str] = None


class MediaSetResponse(MediaSetBase, TimestampMixin):
    """Schema for media set response"""
    id: int
    salon_id: int
    staff_id: int
    client_id: Optional[int] = None
    appointment_id: Optional[int] = None

    # Photos
    before_photo_url: Optional[str] = None
    after_photo_url: Optional[str] = None
    comparison_photo_url: Optional[str] = None
    additional_photos: List[PhotoUpload] = []

    # Services
    services_performed: List[str] = []

    # THE FORMULA VAULT
    color_formulas: List[ColorFormula] = []
    products_used: List[ProductUsed] = []
    techniques_used: List[str] = []

    # Processing details
    total_processing_time: Optional[str] = None
    total_service_time: Optional[str] = None

    # Hair details
    starting_level: Optional[str] = None
    target_level: Optional[str] = None
    achieved_level: Optional[str] = None
    hair_condition_before: Optional[str] = None
    hair_condition_after: Optional[str] = None

    # Tags
    tags: List[str] = []

    # AI generated
    ai_generated_caption: Optional[str] = None
    suggested_hashtags: List[str] = []

    # Consent
    client_photo_consent: bool
    client_social_consent: bool
    client_website_consent: bool

    # Portfolio
    is_portfolio_piece: bool
    is_featured: bool
    is_private: bool
    photo_quality_rating: Optional[int] = None

    # Notes (only for staff)
    stylist_notes: Optional[str] = None
    recommendations: Optional[str] = None
    maintenance_tips: Optional[str] = None

    # Client feedback
    client_satisfaction: Optional[int] = None
    client_feedback: Optional[str] = None

    # Service date
    service_date: Optional[datetime] = None

    # Computed
    has_before_after: bool = False
    can_post_to_social: bool = False
    photo_count: int = 0
    formula_summary: str = ""

    # Expanded relations
    staff_name: Optional[str] = None
    client_name: Optional[str] = None


class MediaSetListResponse(PaginatedResponse[MediaSetResponse]):
    """Paginated list of media sets"""
    pass


class MediaSetSearch(BaseSchema):
    """Media set search parameters"""
    staff_id: Optional[int] = None
    client_id: Optional[int] = None
    tags: Optional[List[str]] = None
    techniques: Optional[List[str]] = None
    has_before_after: Optional[bool] = None
    is_portfolio_piece: Optional[bool] = None
    can_post_to_social: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class GenerateComparisonRequest(BaseSchema):
    """Request to generate comparison photo"""
    media_set_id: int
    layout: str = "side_by_side"  # side_by_side, top_bottom, slider


class FormulaSearch(BaseSchema):
    """Search for formulas"""
    brand: Optional[str] = None
    color: Optional[str] = None
    technique: Optional[str] = None
    starting_level: Optional[str] = None
    target_level: Optional[str] = None
