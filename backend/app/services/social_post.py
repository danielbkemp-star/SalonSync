"""
SocialPost service - Social media publishing
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.models import SocialPost, MediaSet, Salon
from app.models.social_post import PostStatus, SocialPlatform
from app.schemas.social_post import SocialPostCreate, SocialPostUpdate
from app.services.base import BaseService
from app.services.ai_caption import ai_caption_service
from app.app_settings import settings

logger = logging.getLogger(__name__)


class SocialPostService(BaseService[SocialPost, SocialPostCreate, SocialPostUpdate]):
    """Service for social media post operations"""

    def __init__(self):
        super().__init__(SocialPost)

    async def create_from_media_set(
        self,
        db: AsyncSession,
        *,
        media_set: MediaSet,
        platform: str,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None,
        created_by_id: Optional[int] = None
    ) -> SocialPost:
        """Create a social post from a media set"""

        # Use AI-generated caption if not provided
        if not caption and media_set.ai_generated_caption:
            caption = media_set.ai_generated_caption

        if not hashtags and media_set.suggested_hashtags:
            hashtags = media_set.suggested_hashtags

        # Determine media URLs
        media_urls = []
        if media_set.comparison_photo_url:
            media_urls.append({
                "url": media_set.comparison_photo_url,
                "type": "image",
                "public_id": media_set.comparison_photo_public_id
            })
        elif media_set.after_photo_url:
            media_urls.append({
                "url": media_set.after_photo_url,
                "type": "image",
                "public_id": media_set.after_photo_public_id
            })

        # Add additional carousel images if available
        for photo in (media_set.additional_photos or [])[:9]:  # Instagram allows 10 max
            media_urls.append(photo)

        status = PostStatus.SCHEDULED if scheduled_time else PostStatus.DRAFT

        post = SocialPost(
            salon_id=media_set.salon_id,
            media_set_id=media_set.id,
            created_by_id=created_by_id,
            platform=platform,
            caption=caption,
            hashtags=hashtags or [],
            media_urls=media_urls,
            is_carousel=len(media_urls) > 1,
            status=status,
            scheduled_time=scheduled_time,
            caption_generated_by_ai=caption == media_set.ai_generated_caption
        )

        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    async def schedule(
        self,
        db: AsyncSession,
        *,
        post: SocialPost,
        scheduled_time: datetime
    ) -> SocialPost:
        """Schedule a post for future publishing"""
        post.scheduled_time = scheduled_time
        post.status = PostStatus.SCHEDULED

        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    async def publish_now(
        self,
        db: AsyncSession,
        *,
        post: SocialPost,
        salon: Salon
    ) -> SocialPost:
        """Publish a post immediately"""
        post.status = PostStatus.PUBLISHING
        post.publish_attempts += 1
        post.last_attempt_at = datetime.utcnow()

        db.add(post)
        await db.commit()

        try:
            if post.platform == SocialPlatform.INSTAGRAM:
                result = await self._publish_to_instagram(post, salon)
            elif post.platform == SocialPlatform.TIKTOK:
                result = await self._publish_to_tiktok(post, salon)
            else:
                raise ValueError(f"Unsupported platform: {post.platform}")

            # Update with success
            post.status = PostStatus.PUBLISHED
            post.published_time = datetime.utcnow()
            post.platform_post_id = result.get('id')
            post.platform_post_url = result.get('permalink')
            post.platform_response = result
            post.error_message = None

        except Exception as e:
            logger.error(f"Failed to publish post {post.id}: {e}")
            post.status = PostStatus.FAILED
            post.error_message = str(e)

        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    async def _publish_to_instagram(
        self,
        post: SocialPost,
        salon: Salon
    ) -> Dict[str, Any]:
        """Publish to Instagram using Graph API"""
        if not salon.instagram_access_token:
            raise ValueError("Instagram not connected for this salon")

        if not salon.instagram_user_id:
            raise ValueError("Instagram user ID not available")

        async with httpx.AsyncClient() as client:
            # Step 1: Create media container
            if post.is_carousel:
                # Create carousel container
                container_result = await self._create_instagram_carousel(
                    client, post, salon
                )
            else:
                # Create single image container
                media_url = post.media_urls[0]['url'] if post.media_urls else None
                if not media_url:
                    raise ValueError("No media URL for post")

                container_response = await client.post(
                    f"https://graph.facebook.com/v18.0/{salon.instagram_user_id}/media",
                    params={
                        "image_url": media_url,
                        "caption": post.full_caption,
                        "access_token": salon.instagram_access_token
                    }
                )
                container_response.raise_for_status()
                container_result = container_response.json()

            container_id = container_result.get('id')
            if not container_id:
                raise ValueError("Failed to create media container")

            # Step 2: Publish the container
            publish_response = await client.post(
                f"https://graph.facebook.com/v18.0/{salon.instagram_user_id}/media_publish",
                params={
                    "creation_id": container_id,
                    "access_token": salon.instagram_access_token
                }
            )
            publish_response.raise_for_status()
            publish_result = publish_response.json()

            media_id = publish_result.get('id')

            # Step 3: Get permalink
            permalink_response = await client.get(
                f"https://graph.facebook.com/v18.0/{media_id}",
                params={
                    "fields": "permalink",
                    "access_token": salon.instagram_access_token
                }
            )
            permalink_data = permalink_response.json()

            return {
                "id": media_id,
                "permalink": permalink_data.get('permalink'),
                "container_id": container_id
            }

    async def _create_instagram_carousel(
        self,
        client: httpx.AsyncClient,
        post: SocialPost,
        salon: Salon
    ) -> Dict[str, Any]:
        """Create Instagram carousel post"""
        children_ids = []

        # Create container for each media item
        for media in post.media_urls[:10]:  # Instagram max 10
            child_response = await client.post(
                f"https://graph.facebook.com/v18.0/{salon.instagram_user_id}/media",
                params={
                    "image_url": media['url'],
                    "is_carousel_item": "true",
                    "access_token": salon.instagram_access_token
                }
            )
            child_response.raise_for_status()
            children_ids.append(child_response.json()['id'])

        # Create carousel container
        carousel_response = await client.post(
            f"https://graph.facebook.com/v18.0/{salon.instagram_user_id}/media",
            params={
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
                "caption": post.full_caption,
                "access_token": salon.instagram_access_token
            }
        )
        carousel_response.raise_for_status()
        return carousel_response.json()

    async def _publish_to_tiktok(
        self,
        post: SocialPost,
        salon: Salon
    ) -> Dict[str, Any]:
        """Publish to TikTok (placeholder - requires video content)"""
        if not salon.tiktok_access_token:
            raise ValueError("TikTok not connected for this salon")

        # TikTok publishing requires video content and more complex flow
        # This is a placeholder for the actual implementation
        raise NotImplementedError("TikTok publishing not yet implemented")

    async def get_pending_posts(
        self,
        db: AsyncSession,
        *,
        before_time: Optional[datetime] = None
    ) -> List[SocialPost]:
        """Get posts that are scheduled and due for publishing"""
        if before_time is None:
            before_time = datetime.utcnow()

        query = select(SocialPost).where(
            and_(
                SocialPost.status == PostStatus.SCHEDULED,
                SocialPost.scheduled_time <= before_time
            )
        ).order_by(SocialPost.scheduled_time)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_engagement(
        self,
        db: AsyncSession,
        *,
        post: SocialPost,
        salon: Salon
    ) -> SocialPost:
        """Fetch and update engagement metrics from the platform"""
        if post.status != PostStatus.PUBLISHED or not post.platform_post_id:
            return post

        try:
            if post.platform == SocialPlatform.INSTAGRAM:
                metrics = await self._fetch_instagram_metrics(post, salon)

                post.likes = metrics.get('like_count')
                post.comments = metrics.get('comments_count')
                post.saves = metrics.get('saved')
                post.reach = metrics.get('reach')
                post.impressions = metrics.get('impressions')

                # Calculate engagement rate
                if post.reach and post.reach > 0:
                    total_engagement = (post.likes or 0) + (post.comments or 0) + (post.saves or 0)
                    rate = (total_engagement / post.reach) * 100
                    post.engagement_rate = f"{rate:.2f}%"

                post.engagement_updated_at = datetime.utcnow()

                # Record snapshot
                post.record_metrics_snapshot()

        except Exception as e:
            logger.error(f"Failed to fetch metrics for post {post.id}: {e}")

        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    async def _fetch_instagram_metrics(
        self,
        post: SocialPost,
        salon: Salon
    ) -> Dict[str, Any]:
        """Fetch Instagram post metrics"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.facebook.com/v18.0/{post.platform_post_id}",
                params={
                    "fields": "like_count,comments_count",
                    "access_token": salon.instagram_access_token
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_analytics(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get social media analytics for a salon"""
        query = select(SocialPost).where(
            and_(
                SocialPost.salon_id == salon_id,
                SocialPost.status == PostStatus.PUBLISHED,
                SocialPost.published_time >= start_date,
                SocialPost.published_time <= end_date
            )
        )

        result = await db.execute(query)
        posts = list(result.scalars().all())

        # Aggregate metrics
        total_likes = sum(p.likes or 0 for p in posts)
        total_comments = sum(p.comments or 0 for p in posts)
        total_shares = sum(p.shares or 0 for p in posts)
        total_saves = sum(p.saves or 0 for p in posts)
        total_reach = sum(p.reach or 0 for p in posts)
        total_impressions = sum(p.impressions or 0 for p in posts)

        # Posts by platform
        posts_by_platform = {}
        for p in posts:
            platform = p.platform.value if hasattr(p.platform, 'value') else p.platform
            posts_by_platform[platform] = posts_by_platform.get(platform, 0) + 1

        # Average engagement rate
        rates = [
            float(p.engagement_rate.rstrip('%'))
            for p in posts
            if p.engagement_rate
        ]
        avg_engagement_rate = sum(rates) / len(rates) if rates else 0

        # Top posts by engagement
        sorted_posts = sorted(
            posts,
            key=lambda p: p.total_engagement,
            reverse=True
        )[:5]

        return {
            "salon_id": salon_id,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_posts": len(posts),
            "posts_by_platform": posts_by_platform,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "total_saves": total_saves,
            "total_reach": total_reach,
            "total_impressions": total_impressions,
            "average_engagement_rate": avg_engagement_rate,
            "top_posts": [
                {
                    "id": p.id,
                    "platform": p.platform.value if hasattr(p.platform, 'value') else p.platform,
                    "engagement": p.total_engagement,
                    "url": p.platform_post_url
                }
                for p in sorted_posts
            ]
        }


# Singleton instance
social_post_service = SocialPostService()
