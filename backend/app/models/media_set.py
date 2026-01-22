"""
MediaSet model for SalonSync
The core differentiator - captures complete service records including
photos, formulas, products, and links to social posts.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MediaSet(Base):
    """
    Captures the complete service record including before/after photos,
    color formulas, products used, and techniques applied.

    This is the "Formula Vault" - a key differentiator for SalonSync.
    """
    __tablename__ = "media_sets"

    id = Column(Integer, primary_key=True, index=True)

    # Ownership & References
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, unique=True)

    # Title & Description
    title = Column(String(255), nullable=True)  # Optional title for the work
    description = Column(Text, nullable=True)  # Description of the transformation

    # ═══════════════════════════════════════════════════════════════
    # PHOTOS - Stored in Cloudinary
    # ═══════════════════════════════════════════════════════════════

    # Before Photo
    before_photo_url = Column(String(500), nullable=True)
    before_photo_public_id = Column(String(255), nullable=True)  # Cloudinary public_id for management
    before_photo_taken_at = Column(DateTime, nullable=True)

    # After Photo
    after_photo_url = Column(String(500), nullable=True)
    after_photo_public_id = Column(String(255), nullable=True)
    after_photo_taken_at = Column(DateTime, nullable=True)

    # Generated Comparison (side-by-side)
    comparison_photo_url = Column(String(500), nullable=True)
    comparison_photo_public_id = Column(String(255), nullable=True)

    # Additional Photos (process shots, detail shots, styling variations)
    # Structure: [{"url": "...", "public_id": "...", "caption": "...", "type": "process|detail|styling"}]
    additional_photos = Column(JSON, default=list)

    # ═══════════════════════════════════════════════════════════════
    # THE FORMULA VAULT - Key differentiator
    # ═══════════════════════════════════════════════════════════════

    # Services Performed
    services_performed = Column(JSON, default=list)
    # Structure: ["Balayage", "Toner", "Haircut", "Blowout"]

    # Color Formulas - The secret sauce!
    color_formulas = Column(JSON, default=list)
    # Structure: [
    #   {
    #     "zone": "roots",  # roots, mids, ends, all_over, highlights, lowlights, gloss
    #     "brand": "Wella",
    #     "line": "Koleston Perfect",
    #     "color": "6/0",
    #     "developer": "20vol",
    #     "ratio": "1:1",
    #     "processing_time": "35 min",
    #     "heat": false,
    #     "notes": "Applied to regrowth area only"
    #   },
    #   {
    #     "zone": "balayage",
    #     "brand": "Schwarzkopf",
    #     "line": "BlondMe",
    #     "color": "Premium Lift 9+",
    #     "developer": "30vol",
    #     "ratio": "1:2",
    #     "processing_time": "45 min",
    #     "heat": true,
    #     "notes": "Hand-painted, wrapped in film"
    #   }
    # ]

    # Products Used
    products_used = Column(JSON, default=list)
    # Structure: [
    #   {"name": "Olaplex No.1", "brand": "Olaplex", "amount": "5ml", "step": "mixed with lightener"},
    #   {"name": "Olaplex No.2", "brand": "Olaplex", "amount": "full application", "step": "post-lightening"},
    #   {"name": "Purple Shampoo", "brand": "Redken", "amount": "standard", "step": "final rinse"}
    # ]

    # Techniques Used
    techniques_used = Column(JSON, default=list)
    # Structure: ["balayage", "foilayage", "face-framing", "baby lights", "teasy lights"]

    # Processing Details
    total_processing_time = Column(String(100), nullable=True)  # "2 hours 30 min"
    total_service_time = Column(String(100), nullable=True)  # "4 hours"

    # Hair Details (at time of service)
    starting_level = Column(String(50), nullable=True)  # "Level 5 - Light Brown"
    target_level = Column(String(50), nullable=True)  # "Level 9 - Light Blonde"
    achieved_level = Column(String(50), nullable=True)  # "Level 8.5"
    hair_condition_before = Column(String(100), nullable=True)  # "Good", "Damaged", "Virgin"
    hair_condition_after = Column(String(100), nullable=True)
    porosity = Column(String(50), nullable=True)  # "Low", "Medium", "High"

    # ═══════════════════════════════════════════════════════════════
    # SOCIAL MEDIA & MARKETING
    # ═══════════════════════════════════════════════════════════════

    # Tags for categorization and search
    tags = Column(JSON, default=list)
    # Structure: ["transformation", "blonde", "balayage", "dimensional", "bright blonde"]

    # AI-generated caption (optional)
    ai_generated_caption = Column(Text, nullable=True)
    ai_generation_prompt = Column(Text, nullable=True)

    # Hashtag suggestions
    suggested_hashtags = Column(JSON, default=list)

    # ═══════════════════════════════════════════════════════════════
    # CLIENT CONSENT - Critical for photos!
    # ═══════════════════════════════════════════════════════════════

    # Consent tracking
    client_photo_consent = Column(Boolean, default=False)  # Can we keep photos?
    client_social_consent = Column(Boolean, default=False)  # Can we post to social?
    client_website_consent = Column(Boolean, default=False)  # Can we use on website/portfolio?
    consent_recorded_at = Column(DateTime, nullable=True)
    consent_method = Column(String(50), nullable=True)  # "verbal", "written", "digital"

    # ═══════════════════════════════════════════════════════════════
    # PORTFOLIO & VISIBILITY
    # ═══════════════════════════════════════════════════════════════

    # Portfolio features
    is_portfolio_piece = Column(Boolean, default=False)  # Featured in stylist portfolio
    is_featured = Column(Boolean, default=False)  # Featured on salon homepage/gallery
    is_private = Column(Boolean, default=False)  # Only visible to staff, not clients

    # Quality rating (for internal use)
    photo_quality_rating = Column(Integer, nullable=True)  # 1-5 rating

    # ═══════════════════════════════════════════════════════════════
    # NOTES & METADATA
    # ═══════════════════════════════════════════════════════════════

    # Stylist notes
    stylist_notes = Column(Text, nullable=True)  # Private notes about the service
    recommendations = Column(Text, nullable=True)  # Recommendations for next visit
    maintenance_tips = Column(Text, nullable=True)  # Tips shared with client

    # Client feedback
    client_satisfaction = Column(Integer, nullable=True)  # 1-5 rating
    client_feedback = Column(Text, nullable=True)

    # Timestamps
    service_date = Column(DateTime, nullable=True)  # When the service was performed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ═══════════════════════════════════════════════════════════════
    # RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════

    salon = relationship("Salon", back_populates="media_sets")
    staff = relationship("Staff", back_populates="media_sets")
    client = relationship("Client", back_populates="media_sets")
    appointment = relationship("Appointment", back_populates="media_set")
    social_posts = relationship("SocialPost", back_populates="media_set", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MediaSet {self.id} - Staff {self.staff_id}>"

    @property
    def has_before_after(self) -> bool:
        """Check if both before and after photos exist."""
        return bool(self.before_photo_url and self.after_photo_url)

    @property
    def can_post_to_social(self) -> bool:
        """Check if this media set can be posted to social media."""
        return (
            self.has_before_after and
            self.client_social_consent and
            not self.is_private
        )

    @property
    def photo_count(self) -> int:
        """Get total number of photos."""
        count = 0
        if self.before_photo_url:
            count += 1
        if self.after_photo_url:
            count += 1
        if self.comparison_photo_url:
            count += 1
        if self.additional_photos:
            count += len(self.additional_photos)
        return count

    @property
    def formula_summary(self) -> str:
        """Get a brief summary of the color formula."""
        if not self.color_formulas:
            return "No formula recorded"

        formulas = self.color_formulas
        if len(formulas) == 1:
            f = formulas[0]
            return f"{f.get('brand', 'Unknown')} {f.get('color', '')}"
        else:
            return f"{len(formulas)} formulas used"
