"""
SocialPost schemas
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class SocialPostBase(BaseSchema):
    """Base social post fields"""
    platform: str = Field(..., pattern="^(instagram|instagram_stories|instagram_reels|tiktok|facebook)$")
    caption: Optional[str] = None
    hashtags: List[str] = []


class SocialPostCreate(SocialPostBase):
    """Schema for creating a social post"""
    salon_id: int
    media_set_id: Optional[int] = None

    # Media
    media_urls: List[dict] = []  # [{"url": "...", "type": "image|video", "public_id": "..."}]
    is_carousel: bool = False

    # Video specific
    video_url: Optional[str] = None
    video_thumbnail_url: Optional[str] = None

    # Scheduling
    scheduled_time: Optional[datetime] = None  # If None, saves as draft

    # Tagging
    client_instagram_handle: Optional[str] = None
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    product_tags: List[str] = []

    # Notes
    internal_notes: Optional[str] = None


class SocialPostUpdate(BaseSchema):
    """Schema for updating a social post"""
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None

    # Media
    media_urls: Optional[List[dict]] = None

    # Scheduling
    scheduled_time: Optional[datetime] = None

    # Tagging
    client_instagram_handle: Optional[str] = None
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    product_tags: Optional[List[str]] = None

    # Notes
    internal_notes: Optional[str] = None


class SocialPostSchedule(BaseSchema):
    """Schema for scheduling a post"""
    scheduled_time: datetime


class SocialPostResponse(SocialPostBase, TimestampMixin):
    """Schema for social post response"""
    id: int
    salon_id: int
    media_set_id: Optional[int] = None
    created_by_id: Optional[int] = None

    # Media
    media_urls: List[dict] = []
    is_carousel: bool
    video_url: Optional[str] = None
    video_thumbnail_url: Optional[str] = None

    # AI
    caption_generated_by_ai: bool
    caption_edited: bool

    # Status
    status: str
    scheduled_time: Optional[datetime] = None
    published_time: Optional[datetime] = None
    publish_attempts: int

    # Error
    error_message: Optional[str] = None

    # Platform response
    platform_post_id: Optional[str] = None
    platform_post_url: Optional[str] = None

    # Engagement
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    saves: Optional[int] = None
    reach: Optional[int] = None
    impressions: Optional[int] = None
    engagement_rate: Optional[str] = None
    engagement_updated_at: Optional[datetime] = None

    # Tagging
    client_tagged: bool
    client_instagram_handle: Optional[str] = None
    location_name: Optional[str] = None
    product_tags: List[str] = []

    # Approval
    requires_approval: bool
    approved: bool
    approved_at: Optional[datetime] = None

    # Computed
    is_posted: bool = False
    is_pending: bool = True
    can_retry: bool = False
    total_engagement: int = 0
    full_caption: str = ""


class SocialPostListResponse(PaginatedResponse[SocialPostResponse]):
    """Paginated list of social posts"""
    pass


class CaptionGenerate(BaseSchema):
    """Request to generate AI caption"""
    media_set_id: int
    tone: str = "professional"  # professional, casual, fun, luxurious
    include_hashtags: bool = True
    hashtag_count: int = Field(15, ge=5, le=30)
    include_call_to_action: bool = True
    mention_products: bool = False
    custom_instructions: Optional[str] = None


class CaptionGenerateResponse(BaseSchema):
    """AI generated caption response"""
    caption: str
    hashtags: List[str]
    suggested_post_time: Optional[datetime] = None
    confidence_score: Optional[float] = None


class SocialPostPublish(BaseSchema):
    """Request to publish a post immediately"""
    post_id: int


class SocialPostBulkSchedule(BaseSchema):
    """Bulk schedule multiple posts"""
    post_ids: List[int]
    start_time: datetime
    interval_hours: int = Field(24, ge=1, le=168)  # Time between posts


class SocialAnalytics(BaseSchema):
    """Social media analytics"""
    salon_id: int
    period_start: datetime
    period_end: datetime

    # Post counts
    total_posts: int
    posts_by_platform: dict  # {"instagram": 10, "tiktok": 5}

    # Engagement
    total_likes: int
    total_comments: int
    total_shares: int
    total_saves: int
    average_engagement_rate: float

    # Reach
    total_reach: int
    total_impressions: int

    # Top performing
    top_posts: List[dict]  # Top 5 by engagement


class BestTimeToPost(BaseSchema):
    """Best times to post analysis"""
    salon_id: int
    platform: str
    best_days: List[str]  # ["Monday", "Wednesday", "Friday"]
    best_hours: List[int]  # [9, 12, 18]
    recommended_times: List[datetime]  # Next 7 recommended post times
