"""
Social Post API routes
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, SocialPost, MediaSet, Salon
from app.models.social_post import PostStatus
from app.schemas.social_post import (
    SocialPostCreate, SocialPostUpdate, SocialPostResponse,
    SocialPostSchedule, CaptionGenerate, CaptionGenerateResponse
)
from app.schemas.base import MessageResponse
from app.services.social_post import social_post_service
from app.services.media_set import media_set_service
from app.services.salon import salon_service
from app.services.ai_caption import ai_caption_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/social-posts", tags=["Social Posts"])


@router.post("", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
async def create_social_post(
    post_in: SocialPostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new social post"""
    post = await social_post_service.create(db, obj_in=post_in)
    return post


@router.post("/from-media-set/{media_set_id}", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
async def create_post_from_media_set(
    media_set_id: int,
    platform: str = Query(..., pattern="^(instagram|instagram_stories|instagram_reels|tiktok|facebook)$"),
    caption: Optional[str] = None,
    hashtags: Optional[List[str]] = Query(None),
    scheduled_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a social post from an existing media set"""
    media_set = await media_set_service.get(db, media_set_id)
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    if not media_set.can_post_to_social:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media set does not have social posting consent or is private"
        )

    post = await social_post_service.create_from_media_set(
        db,
        media_set=media_set,
        platform=platform,
        caption=caption,
        hashtags=hashtags,
        scheduled_time=scheduled_time,
        created_by_id=current_user.id
    )
    return post


@router.get("/{post_id}", response_model=SocialPostResponse)
async def get_social_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get social post by ID"""
    post = await social_post_service.get(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post


@router.get("/salon/{salon_id}", response_model=List[SocialPostResponse])
async def list_social_posts(
    salon_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(draft|scheduled|publishing|published|failed)$"),
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List social posts for a salon"""
    filters = {"salon_id": salon_id}
    if status:
        filters["status"] = status
    if platform:
        filters["platform"] = platform

    posts = await social_post_service.get_multi(
        db, skip=skip, limit=limit, filters=filters, order_by="created_at", order_desc=True
    )
    return posts


@router.patch("/{post_id}", response_model=SocialPostResponse)
async def update_social_post(
    post_id: int,
    post_in: SocialPostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a social post (only drafts and scheduled can be edited)"""
    post = await social_post_service.get(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.status not in [PostStatus.DRAFT, PostStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a post that is already publishing or published"
        )

    # Mark as edited if AI caption was modified
    if post_in.caption and post.caption_generated_by_ai:
        post.caption_edited = True
        post.original_ai_caption = post.caption

    post = await social_post_service.update(db, db_obj=post, obj_in=post_in)
    return post


@router.post("/{post_id}/schedule", response_model=SocialPostResponse)
async def schedule_post(
    post_id: int,
    schedule: SocialPostSchedule,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule a post for future publishing"""
    post = await social_post_service.get(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.status not in [PostStatus.DRAFT, PostStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only schedule draft or already-scheduled posts"
        )

    if schedule.scheduled_time <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future"
        )

    post = await social_post_service.schedule(
        db, post=post, scheduled_time=schedule.scheduled_time
    )
    return post


@router.post("/{post_id}/publish", response_model=SocialPostResponse)
async def publish_post_now(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Publish a post immediately"""
    post = await social_post_service.get(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post is already published"
        )

    if post.status == PostStatus.PUBLISHING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post is currently being published"
        )

    # Get salon for social media credentials
    salon = await salon_service.get(db, post.salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    post = await social_post_service.publish_now(db, post=post, salon=salon)

    if post.status == PostStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish: {post.error_message}"
        )

    return post


@router.post("/{post_id}/retry", response_model=SocialPostResponse)
async def retry_failed_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retry publishing a failed post"""
    post = await social_post_service.get(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if not post.can_retry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post cannot be retried (max attempts reached or not in failed state)"
        )

    salon = await salon_service.get(db, post.salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    post = await social_post_service.publish_now(db, post=post, salon=salon)
    return post


@router.post("/{post_id}/refresh-metrics", response_model=SocialPostResponse)
async def refresh_engagement_metrics(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch latest engagement metrics for a published post"""
    post = await social_post_service.get(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.status != PostStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refresh metrics for published posts"
        )

    salon = await salon_service.get(db, post.salon_id)
    if not salon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )

    post = await social_post_service.update_engagement(db, post=post, salon=salon)
    return post


@router.get("/salon/{salon_id}/analytics")
async def get_social_analytics(
    salon_id: int,
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get social media analytics for a salon"""
    analytics = await social_post_service.get_analytics(
        db, salon_id,
        start_date=start_date,
        end_date=end_date
    )
    return analytics


@router.post("/generate-caption", response_model=CaptionGenerateResponse)
async def generate_caption(
    request: CaptionGenerate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI caption for a media set"""
    media_set = await media_set_service.get(db, request.media_set_id)
    if not media_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media set not found"
        )

    if not ai_caption_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI caption service not configured"
        )

    result = await ai_caption_service.generate_caption(
        services_performed=media_set.services_performed or [],
        techniques_used=media_set.techniques_used or [],
        color_formulas=media_set.color_formulas,
        starting_level=media_set.starting_level,
        achieved_level=media_set.achieved_level,
        tags=media_set.tags,
        tone=request.tone,
        include_hashtags=request.include_hashtags,
        hashtag_count=request.hashtag_count,
        include_call_to_action=request.include_call_to_action,
        mention_products=request.mention_products,
        products_used=media_set.products_used,
        custom_instructions=request.custom_instructions
    )

    return CaptionGenerateResponse(
        caption=result['caption'],
        hashtags=result['hashtags']
    )


@router.delete("/{post_id}", response_model=MessageResponse)
async def delete_social_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a social post (only drafts and scheduled)"""
    post = await social_post_service.get(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a published post. It must be deleted from the platform directly."
        )

    await social_post_service.delete(db, id=post_id)
    return MessageResponse(message="Post deleted successfully")
