"""
SocialPost model for SalonSync
Manages social media posts across platforms (Instagram, TikTok, Facebook)
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class PostStatus(str, enum.Enum):
    """Status of a social media post"""
    DRAFT = "draft"  # Not yet ready to post
    SCHEDULED = "scheduled"  # Scheduled for future posting
    PUBLISHING = "publishing"  # Currently being published
    PUBLISHED = "published"  # Successfully posted
    FAILED = "failed"  # Failed to post
    DELETED = "deleted"  # Deleted from platform


class SocialPlatform(str, enum.Enum):
    """Supported social media platforms"""
    INSTAGRAM = "instagram"
    INSTAGRAM_STORIES = "instagram_stories"
    INSTAGRAM_REELS = "instagram_reels"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"


class SocialPost(Base):
    """
    Social media post record.
    Tracks posts across platforms, including scheduling, publishing status,
    and engagement metrics.
    """
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)

    # Ownership
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)
    media_set_id = Column(Integer, ForeignKey("media_sets.id"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Platform
    platform = Column(
        Enum(SocialPlatform, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )

    # ═══════════════════════════════════════════════════════════════
    # CONTENT
    # ═══════════════════════════════════════════════════════════════

    # Caption/Text
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, default=list)  # ["hairtransformation", "balayage", "salonlife"]

    # Media to post (can differ from media_set)
    media_urls = Column(JSON, default=list)  # URLs of images/videos to post
    # Structure: [{"url": "...", "type": "image|video", "public_id": "..."}]

    # For carousel posts
    is_carousel = Column(Boolean, default=False)
    carousel_order = Column(JSON, default=list)  # Order of media items

    # For video posts
    video_url = Column(String(500), nullable=True)
    video_thumbnail_url = Column(String(500), nullable=True)
    video_duration_seconds = Column(Integer, nullable=True)

    # ═══════════════════════════════════════════════════════════════
    # AI GENERATION
    # ═══════════════════════════════════════════════════════════════

    # AI caption generation tracking
    caption_generated_by_ai = Column(Boolean, default=False)
    ai_generation_prompt = Column(Text, nullable=True)
    ai_model_used = Column(String(100), nullable=True)  # "claude-3-sonnet", "gpt-4", etc.
    ai_generation_timestamp = Column(DateTime, nullable=True)

    # User edits to AI caption
    original_ai_caption = Column(Text, nullable=True)  # Before user edits
    caption_edited = Column(Boolean, default=False)

    # ═══════════════════════════════════════════════════════════════
    # SCHEDULING & PUBLISHING
    # ═══════════════════════════════════════════════════════════════

    # Status
    status = Column(
        Enum(PostStatus, values_callable=lambda x: [e.value for e in x]),
        default=PostStatus.DRAFT,
        index=True
    )

    # Timing
    scheduled_time = Column(DateTime, nullable=True, index=True)
    published_time = Column(DateTime, nullable=True)
    publish_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)

    # ═══════════════════════════════════════════════════════════════
    # PLATFORM RESPONSE
    # ═══════════════════════════════════════════════════════════════

    # Platform identifiers
    platform_post_id = Column(String(255), nullable=True, index=True)  # ID on the platform
    platform_post_url = Column(String(500), nullable=True)  # Direct link to post
    platform_media_id = Column(String(255), nullable=True)  # For Instagram container ID

    # Full API response (for debugging)
    platform_response = Column(JSON, nullable=True)

    # ═══════════════════════════════════════════════════════════════
    # ENGAGEMENT METRICS
    # ═══════════════════════════════════════════════════════════════

    # Core metrics
    likes = Column(Integer, nullable=True)
    comments = Column(Integer, nullable=True)
    shares = Column(Integer, nullable=True)
    saves = Column(Integer, nullable=True)

    # Reach & Impressions
    reach = Column(Integer, nullable=True)
    impressions = Column(Integer, nullable=True)

    # Video specific
    video_views = Column(Integer, nullable=True)
    video_watch_time_seconds = Column(Integer, nullable=True)
    avg_watch_percentage = Column(Integer, nullable=True)

    # Story/Reel specific
    replies = Column(Integer, nullable=True)
    exits = Column(Integer, nullable=True)
    taps_forward = Column(Integer, nullable=True)
    taps_back = Column(Integer, nullable=True)

    # Engagement tracking
    engagement_rate = Column(String(10), nullable=True)  # Calculated percentage
    engagement_updated_at = Column(DateTime, nullable=True)

    # Historical metrics (track changes over time)
    metrics_history = Column(JSON, default=list)
    # Structure: [{"date": "2024-01-15", "likes": 100, "comments": 5, "reach": 500}, ...]

    # ═══════════════════════════════════════════════════════════════
    # TAGGING & MENTIONS
    # ═══════════════════════════════════════════════════════════════

    # Client tagging
    client_tagged = Column(Boolean, default=False)
    client_instagram_handle = Column(String(100), nullable=True)

    # Location tagging
    location_id = Column(String(255), nullable=True)  # Platform's location ID
    location_name = Column(String(255), nullable=True)

    # Product/brand mentions
    product_tags = Column(JSON, default=list)  # ["@olaplex", "@wlobalcolor"]

    # ═══════════════════════════════════════════════════════════════
    # APPROVAL WORKFLOW
    # ═══════════════════════════════════════════════════════════════

    # For salons that require owner approval before posting
    requires_approval = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # ═══════════════════════════════════════════════════════════════
    # METADATA
    # ═══════════════════════════════════════════════════════════════

    # Notes
    internal_notes = Column(Text, nullable=True)  # For internal tracking

    # Best time to post suggestion
    suggested_post_time = Column(DateTime, nullable=True)
    suggestion_reason = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ═══════════════════════════════════════════════════════════════
    # RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════

    salon = relationship("Salon", back_populates="social_posts")
    media_set = relationship("MediaSet", back_populates="social_posts")

    def __repr__(self):
        return f"<SocialPost {self.id} - {self.platform.value} - {self.status.value}>"

    @property
    def is_posted(self) -> bool:
        """Check if post has been published."""
        return self.status == PostStatus.PUBLISHED and self.platform_post_id is not None

    @property
    def is_pending(self) -> bool:
        """Check if post is waiting to be published."""
        return self.status in [PostStatus.DRAFT, PostStatus.SCHEDULED]

    @property
    def can_retry(self) -> bool:
        """Check if a failed post can be retried."""
        return self.status == PostStatus.FAILED and self.publish_attempts < 3

    @property
    def full_caption(self) -> str:
        """Get caption with hashtags appended."""
        caption = self.caption or ""
        if self.hashtags:
            hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in self.hashtags)
            return f"{caption}\n\n{hashtag_str}".strip()
        return caption

    @property
    def total_engagement(self) -> int:
        """Get total engagement count."""
        return sum(filter(None, [
            self.likes,
            self.comments,
            self.shares,
            self.saves,
        ]))

    def record_metrics_snapshot(self):
        """Record current metrics to history."""
        if not self.metrics_history:
            self.metrics_history = []

        snapshot = {
            "date": datetime.utcnow().isoformat(),
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "saves": self.saves,
            "reach": self.reach,
            "impressions": self.impressions,
        }
        self.metrics_history.append(snapshot)
