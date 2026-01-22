"""
Social Media API Routes for SalonSync
Social posts, publishing, scheduling, and analytics
"""

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import SocialPost, MediaSet, Salon
from app.models.social_post import PostStatus, SocialPlatform
from app.schemas.social_post import (
    SocialPostCreate, SocialPostUpdate, SocialPostResponse, SocialPostListResponse,
    SocialPostSchedule, CaptionGenerate, CaptionGenerateResponse,
    SocialPostPublish, SocialPostBulkSchedule, SocialAnalytics, BestTimeToPost
)
from app.schemas.base import MessageResponse, PaginatedResponse
from app.api.dependencies import (
    CurrentUser, require_salon_access, SalonAccess
)
from app.services.ai_caption import ai_caption_service
from app.services.content_service import content_service
from app.services.instagram_service import instagram_service

router = APIRouter()


# ============================================================================
# CRUD Operations
# ============================================================================

@router.post("/salons/{salon_id}/social-posts", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
async def create_social_post(
    salon_id: int,
    post_in: SocialPostCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Create a new social media post.

    Can be saved as draft or scheduled for later.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    # Verify media set if provided
    if post_in.media_set_id:
        media_set = db.query(MediaSet).filter(
            MediaSet.id == post_in.media_set_id,
            MediaSet.salon_id == salon_id
        ).first()
        if not media_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media set not found"
            )
        # Check consent
        if not media_set.client_social_consent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client has not consented to social media posting"
            )

    # Determine initial status
    if post_in.scheduled_time:
        initial_status = PostStatus.SCHEDULED
    else:
        initial_status = PostStatus.DRAFT

    post = SocialPost(
        salon_id=salon_id,
        media_set_id=post_in.media_set_id,
        created_by_id=current_user.id,
        platform=post_in.platform,
        caption=post_in.caption,
        hashtags=post_in.hashtags,
        media_urls=post_in.media_urls,
        is_carousel=post_in.is_carousel,
        video_url=post_in.video_url,
        video_thumbnail_url=post_in.video_thumbnail_url,
        status=initial_status,
        scheduled_time=post_in.scheduled_time,
        client_instagram_handle=post_in.client_instagram_handle,
        location_id=post_in.location_id,
        location_name=post_in.location_name,
        product_tags=post_in.product_tags,
        internal_notes=post_in.internal_notes,
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return _post_to_response(post)


@router.get("/salons/{salon_id}/social-posts", response_model=SocialPostListResponse)
async def list_social_posts(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    platform: Optional[str] = None,
):
    """List social posts for a salon."""
    salon = await require_salon_access(salon_id, current_user, db)

    query = db.query(SocialPost).filter(SocialPost.salon_id == salon_id)

    if status:
        query = query.filter(SocialPost.status == status)

    if platform:
        query = query.filter(SocialPost.platform == platform)

    total = query.count()
    posts = query.order_by(SocialPost.created_at.desc()).offset(skip).limit(limit).all()

    items = [_post_to_response(p) for p in posts]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/social-posts/{post_id}", response_model=SocialPostResponse)
async def get_social_post(
    post_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get social post by ID."""
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social post not found"
        )

    await require_salon_access(post.salon_id, current_user, db)

    return _post_to_response(post)


@router.put("/social-posts/{post_id}", response_model=SocialPostResponse)
async def update_social_post(
    post_id: int,
    post_in: SocialPostUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Update social post."""
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social post not found"
        )

    await require_salon_access(post.salon_id, current_user, db)

    # Can't edit published posts
    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit published posts"
        )

    # Update fields
    update_data = post_in.model_dump(exclude_unset=True)

    # Track if caption was edited
    if 'caption' in update_data and post.caption_generated_by_ai:
        post.caption_edited = True

    for field, value in update_data.items():
        if hasattr(post, field):
            setattr(post, field, value)

    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)

    return _post_to_response(post)


@router.delete("/social-posts/{post_id}")
async def delete_social_post(
    post_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Delete social post."""
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social post not found"
        )

    await require_salon_access(post.salon_id, current_user, db)

    db.delete(post)
    db.commit()

    return MessageResponse(message="Social post deleted successfully")


# ============================================================================
# Caption Generation
# ============================================================================

@router.post("/social-posts/{post_id}/generate-caption", response_model=CaptionGenerateResponse)
async def generate_post_caption(
    post_id: int,
    request: CaptionGenerate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Generate AI caption for a social post."""
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social post not found"
        )

    await require_salon_access(post.salon_id, current_user, db)

    # Get media set context if available
    context = {}
    if post.media_set_id:
        media_set = db.query(MediaSet).filter(MediaSet.id == post.media_set_id).first()
        if media_set:
            context = {
                "services": media_set.services_performed or [],
                "techniques": media_set.techniques_used or [],
                "formulas": media_set.color_formulas or [],
                "tags": media_set.tags or [],
                "has_before_after": bool(media_set.before_photo_url and media_set.after_photo_url),
            }

    result = ai_caption_service.generate_caption(
        context=context,
        tone=request.tone,
        include_hashtags=request.include_hashtags,
        hashtag_count=request.hashtag_count,
        include_call_to_action=request.include_call_to_action,
        custom_instructions=request.custom_instructions,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate caption"
        )

    # Update post with generated caption
    post.caption = result.get("caption")
    post.hashtags = result.get("hashtags", [])
    post.caption_generated_by_ai = True
    post.caption_edited = False
    post.updated_at = datetime.utcnow()
    db.commit()

    return CaptionGenerateResponse(
        caption=result.get("caption", ""),
        hashtags=result.get("hashtags", []),
        suggested_post_time=result.get("suggested_post_time"),
        confidence_score=result.get("confidence_score"),
    )


# ============================================================================
# Publishing
# ============================================================================

@router.post("/social-posts/{post_id}/publish")
async def publish_post(
    post_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Publish a social post immediately.

    Requires salon to have connected social accounts.
    """
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social post not found"
        )

    salon = await SalonAccess(require_manager=True)(post.salon_id, current_user, db)

    # Check if already published
    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post is already published"
        )

    # Verify social account is connected
    if post.platform in ["instagram", "instagram_stories", "instagram_reels"]:
        if not salon.instagram_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instagram account not connected"
            )
    elif post.platform == "tiktok":
        if not salon.tiktok_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TikTok account not connected"
            )

    # Attempt to publish via platform API
    try:
        if post.platform in ["instagram", "instagram_stories", "instagram_reels"]:
            if instagram_service.is_configured and salon.instagram_access_token:
                # Get image URLs from media set if available
                image_urls = []
                if post.media_set_id:
                    media_set = db.query(MediaSet).filter(MediaSet.id == post.media_set_id).first()
                    if media_set:
                        if media_set.comparison_photo_url:
                            image_urls.append(media_set.comparison_photo_url)
                        elif media_set.before_photo_url and media_set.after_photo_url:
                            image_urls = [media_set.before_photo_url, media_set.after_photo_url]
                        elif media_set.after_photo_url:
                            image_urls.append(media_set.after_photo_url)

                if image_urls:
                    # Build full caption with hashtags
                    full_caption = post.caption or ""
                    if post.hashtags:
                        hashtag_str = " ".join(f"#{h}" for h in post.hashtags)
                        full_caption = f"{full_caption}\n\n.\n.\n.\n{hashtag_str}"

                    if len(image_urls) == 1:
                        result = await instagram_service.publish_single_image(
                            salon.instagram_access_token,
                            salon.instagram_user_id,
                            image_urls[0],
                            full_caption
                        )
                    else:
                        result = await instagram_service.publish_carousel(
                            salon.instagram_access_token,
                            salon.instagram_user_id,
                            image_urls,
                            full_caption
                        )

                    post.platform_post_id = result.get("media_id")
                    post.platform_post_url = result.get("permalink")
                    post.status = PostStatus.PUBLISHED
                    post.published_time = datetime.utcnow()
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No images available to publish"
                    )
            else:
                # Instagram service not configured - simulate
                post.status = PostStatus.PUBLISHED
                post.published_time = datetime.utcnow()
                post.platform_post_id = f"simulated_{post.id}_{datetime.utcnow().timestamp()}"
                post.platform_post_url = f"https://instagram.com/p/{post.platform_post_id}"
        else:
            # Other platforms - simulate for now
            post.status = PostStatus.PUBLISHED
            post.published_time = datetime.utcnow()
            post.platform_post_id = f"simulated_{post.id}_{datetime.utcnow().timestamp()}"
            post.platform_post_url = f"https://{post.platform}.com/posts/{post.platform_post_id}"

        post.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(post)

        return {
            "message": "Post published successfully",
            "post_id": post.platform_post_id,
            "post_url": post.platform_post_url,
            "platform": post.platform
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish: {str(e)}"
        )


@router.post("/social-posts/{post_id}/schedule")
async def schedule_post(
    post_id: int,
    schedule: SocialPostSchedule,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Schedule a post for later publishing."""
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social post not found"
        )

    await require_salon_access(post.salon_id, current_user, db)

    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule published posts"
        )

    # Validate scheduled time is in the future
    if schedule.scheduled_time <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future"
        )

    post.scheduled_time = schedule.scheduled_time
    post.status = PostStatus.SCHEDULED
    post.updated_at = datetime.utcnow()
    db.commit()

    return MessageResponse(message=f"Post scheduled for {schedule.scheduled_time}")


# ============================================================================
# Analytics & Insights
# ============================================================================

@router.get("/social-posts/{post_id}/insights")
async def get_post_insights(
    post_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get engagement insights for a published post."""
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social post not found"
        )

    await require_salon_access(post.salon_id, current_user, db)

    if post.status != PostStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insights only available for published posts"
        )

    # TODO: Fetch real insights from platform API
    # For now, return stored engagement data
    return {
        "post_id": post.id,
        "platform": post.platform,
        "published_time": post.published_time,
        "engagement": {
            "likes": post.likes or 0,
            "comments": post.comments or 0,
            "shares": post.shares or 0,
            "saves": post.saves or 0,
            "reach": post.reach or 0,
            "impressions": post.impressions or 0,
            "engagement_rate": post.engagement_rate,
        },
        "last_updated": post.engagement_updated_at,
    }


@router.get("/salons/{salon_id}/social-analytics", response_model=SocialAnalytics)
async def get_salon_analytics(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    days: int = Query(30, ge=7, le=90),
):
    """Get social media analytics for the salon."""
    salon = await require_salon_access(salon_id, current_user, db)

    period_start = datetime.utcnow() - timedelta(days=days)
    period_end = datetime.utcnow()

    # Query published posts in period
    posts = db.query(SocialPost).filter(
        SocialPost.salon_id == salon_id,
        SocialPost.status == PostStatus.PUBLISHED,
        SocialPost.published_time >= period_start
    ).all()

    # Calculate metrics
    total_posts = len(posts)
    posts_by_platform = {}
    total_likes = 0
    total_comments = 0
    total_shares = 0
    total_saves = 0
    total_reach = 0
    total_impressions = 0

    for post in posts:
        platform = post.platform
        posts_by_platform[platform] = posts_by_platform.get(platform, 0) + 1
        total_likes += post.likes or 0
        total_comments += post.comments or 0
        total_shares += post.shares or 0
        total_saves += post.saves or 0
        total_reach += post.reach or 0
        total_impressions += post.impressions or 0

    # Calculate average engagement rate
    total_engagement = total_likes + total_comments + total_shares + total_saves
    avg_engagement_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0

    # Get top performing posts
    top_posts = sorted(
        posts,
        key=lambda p: (p.likes or 0) + (p.comments or 0) + (p.shares or 0),
        reverse=True
    )[:5]

    top_posts_data = [
        {
            "id": p.id,
            "platform": p.platform,
            "published_time": p.published_time,
            "likes": p.likes,
            "comments": p.comments,
            "engagement_rate": p.engagement_rate,
        }
        for p in top_posts
    ]

    return SocialAnalytics(
        salon_id=salon_id,
        period_start=period_start,
        period_end=period_end,
        total_posts=total_posts,
        posts_by_platform=posts_by_platform,
        total_likes=total_likes,
        total_comments=total_comments,
        total_shares=total_shares,
        total_saves=total_saves,
        average_engagement_rate=avg_engagement_rate,
        total_reach=total_reach,
        total_impressions=total_impressions,
        top_posts=top_posts_data,
    )


@router.get("/salons/{salon_id}/best-times-to-post", response_model=BestTimeToPost)
async def get_best_times_to_post(
    salon_id: int,
    platform: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Get recommended best times to post based on historical engagement.
    """
    salon = await require_salon_access(salon_id, current_user, db)

    # TODO: Analyze historical data for actual recommendations
    # For now, return industry standard recommendations

    best_days = ["Tuesday", "Wednesday", "Thursday"]
    best_hours = [9, 12, 18]  # 9am, 12pm, 6pm

    # Generate next 7 recommended times
    now = datetime.utcnow()
    recommended_times = []

    for i in range(7):
        day = now + timedelta(days=i)
        day_name = day.strftime("%A")
        if day_name in best_days:
            for hour in best_hours:
                post_time = day.replace(hour=hour, minute=0, second=0, microsecond=0)
                if post_time > now:
                    recommended_times.append(post_time)
                    if len(recommended_times) >= 7:
                        break
        if len(recommended_times) >= 7:
            break

    return BestTimeToPost(
        salon_id=salon_id,
        platform=platform,
        best_days=best_days,
        best_hours=best_hours,
        recommended_times=recommended_times[:7],
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _post_to_response(post: SocialPost) -> SocialPostResponse:
    """Convert SocialPost model to SocialPostResponse schema."""
    # Computed fields
    is_posted = post.status == PostStatus.PUBLISHED
    is_pending = post.status in [PostStatus.DRAFT, PostStatus.SCHEDULED]
    can_retry = post.status == PostStatus.FAILED and post.publish_attempts < 3

    total_engagement = (
        (post.likes or 0) +
        (post.comments or 0) +
        (post.shares or 0) +
        (post.saves or 0)
    )

    # Build full caption with hashtags
    full_caption = post.caption or ""
    if post.hashtags:
        hashtag_str = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in post.hashtags])
        full_caption = f"{full_caption}\n\n{hashtag_str}".strip()

    return SocialPostResponse(
        id=post.id,
        salon_id=post.salon_id,
        media_set_id=post.media_set_id,
        created_by_id=post.created_by_id,
        platform=post.platform,
        caption=post.caption,
        hashtags=post.hashtags or [],
        media_urls=post.media_urls or [],
        is_carousel=post.is_carousel,
        video_url=post.video_url,
        video_thumbnail_url=post.video_thumbnail_url,
        caption_generated_by_ai=post.caption_generated_by_ai,
        caption_edited=post.caption_edited,
        status=post.status.value if post.status else "draft",
        scheduled_time=post.scheduled_time,
        published_time=post.published_time,
        publish_attempts=post.publish_attempts,
        error_message=post.error_message,
        platform_post_id=post.platform_post_id,
        platform_post_url=post.platform_post_url,
        likes=post.likes,
        comments=post.comments,
        shares=post.shares,
        saves=post.saves,
        reach=post.reach,
        impressions=post.impressions,
        engagement_rate=post.engagement_rate,
        engagement_updated_at=post.engagement_updated_at,
        client_tagged=bool(post.client_instagram_handle),
        client_instagram_handle=post.client_instagram_handle,
        location_name=post.location_name,
        product_tags=post.product_tags or [],
        requires_approval=post.requires_approval,
        approved=post.approved,
        approved_at=post.approved_at,
        is_posted=is_posted,
        is_pending=is_pending,
        can_retry=can_retry,
        total_engagement=total_engagement,
        full_caption=full_caption,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )
