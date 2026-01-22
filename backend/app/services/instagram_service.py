"""
Instagram Service - Instagram Graph API integration
Handles OAuth, publishing, and insights for Business accounts
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from urllib.parse import urlencode
import httpx

from app.app_settings import settings

logger = logging.getLogger(__name__)


# Instagram Graph API endpoints
INSTAGRAM_AUTH_URL = "https://api.instagram.com/oauth/authorize"
INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
INSTAGRAM_GRAPH_URL = "https://graph.instagram.com"
FACEBOOK_GRAPH_URL = "https://graph.facebook.com/v18.0"


class InstagramService:
    """
    Instagram Graph API service for Business/Creator accounts.

    Note: Publishing requires app review and approval from Meta.
    This implementation handles the full flow once approved.
    """

    def __init__(self):
        self.client_id = settings.INSTAGRAM_APP_ID
        self.client_secret = settings.INSTAGRAM_APP_SECRET
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def get_auth_url(
        self,
        salon_id: int,
        redirect_uri: str,
        *,
        scopes: Optional[List[str]] = None
    ) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            salon_id: Salon ID (stored in state for callback)
            redirect_uri: OAuth redirect URI
            scopes: Permission scopes to request

        Returns:
            Authorization URL to redirect user to
        """
        if not self.is_configured:
            raise RuntimeError("Instagram API not configured")

        if scopes is None:
            # Default scopes for publishing and insights
            scopes = [
                "instagram_basic",
                "instagram_content_publish",
                "instagram_manage_comments",
                "instagram_manage_insights",
                "pages_show_list",
                "pages_read_engagement"
            ]

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": ",".join(scopes),
            "response_type": "code",
            "state": f"salon_{salon_id}"  # Used to identify salon on callback
        }

        return f"{INSTAGRAM_AUTH_URL}?{urlencode(params)}"

    async def handle_callback(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect URI used in auth request

        Returns:
            Dict with access_token, user_id, and other metadata
        """
        if not self.is_configured:
            raise RuntimeError("Instagram API not configured")

        client = await self._get_client()

        # Exchange code for short-lived token
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code
        }

        response = await client.post(INSTAGRAM_TOKEN_URL, data=token_data)
        response.raise_for_status()
        short_lived = response.json()

        # Exchange for long-lived token (60 days)
        long_lived_params = {
            "grant_type": "ig_exchange_token",
            "client_secret": self.client_secret,
            "access_token": short_lived["access_token"]
        }

        long_response = await client.get(
            f"{INSTAGRAM_GRAPH_URL}/access_token",
            params=long_lived_params
        )
        long_response.raise_for_status()
        long_lived = long_response.json()

        # Get user profile info
        profile = await self.get_profile(long_lived["access_token"])

        return {
            "access_token": long_lived["access_token"],
            "token_type": "long_lived",
            "expires_in": long_lived.get("expires_in", 5184000),  # ~60 days
            "expires_at": (datetime.utcnow() + timedelta(seconds=long_lived.get("expires_in", 5184000))).isoformat(),
            "user_id": short_lived["user_id"],
            "instagram_user_id": short_lived["user_id"],
            "username": profile.get("username"),
            "account_type": profile.get("account_type"),
            "media_count": profile.get("media_count")
        }

    async def refresh_token(self, access_token: str) -> Dict[str, Any]:
        """
        Refresh a long-lived token before it expires.
        Can be done when token has more than 24 hours but less than 60 days left.

        Args:
            access_token: Current long-lived access token

        Returns:
            New token data
        """
        client = await self._get_client()

        params = {
            "grant_type": "ig_refresh_token",
            "access_token": access_token
        }

        response = await client.get(
            f"{INSTAGRAM_GRAPH_URL}/refresh_access_token",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        return {
            "access_token": data["access_token"],
            "token_type": "long_lived",
            "expires_in": data.get("expires_in", 5184000),
            "expires_at": (datetime.utcnow() + timedelta(seconds=data.get("expires_in", 5184000))).isoformat()
        }

    async def get_profile(self, access_token: str) -> Dict[str, Any]:
        """Get Instagram user profile information."""
        client = await self._get_client()

        params = {
            "fields": "id,username,account_type,media_count",
            "access_token": access_token
        }

        response = await client.get(f"{INSTAGRAM_GRAPH_URL}/me", params=params)
        response.raise_for_status()
        return response.json()

    async def publish_single_image(
        self,
        access_token: str,
        instagram_user_id: str,
        image_url: str,
        caption: str,
        *,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish a single image to Instagram.

        Note: Requires instagram_content_publish permission (needs app review).

        Args:
            access_token: User's access token
            instagram_user_id: Instagram user ID
            image_url: Public URL of image (must be accessible by Instagram)
            caption: Post caption
            location_id: Optional Facebook Page location ID

        Returns:
            Dict with media_id and permalink
        """
        client = await self._get_client()

        # Step 1: Create media container
        container_data = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token
        }

        if location_id:
            container_data["location_id"] = location_id

        container_response = await client.post(
            f"{INSTAGRAM_GRAPH_URL}/{instagram_user_id}/media",
            data=container_data
        )
        container_response.raise_for_status()
        container = container_response.json()

        container_id = container["id"]

        # Step 2: Check container status (may need to wait for processing)
        await self._wait_for_container(access_token, container_id)

        # Step 3: Publish the container
        publish_response = await client.post(
            f"{INSTAGRAM_GRAPH_URL}/{instagram_user_id}/media_publish",
            data={
                "creation_id": container_id,
                "access_token": access_token
            }
        )
        publish_response.raise_for_status()
        published = publish_response.json()

        # Get the media details
        media_details = await self.get_media_details(access_token, published["id"])

        return {
            "media_id": published["id"],
            "permalink": media_details.get("permalink"),
            "timestamp": media_details.get("timestamp"),
            "status": "published"
        }

    async def publish_carousel(
        self,
        access_token: str,
        instagram_user_id: str,
        image_urls: List[str],
        caption: str,
        *,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish a carousel (multiple images) to Instagram.
        Perfect for before/after transformations.

        Args:
            access_token: User's access token
            instagram_user_id: Instagram user ID
            image_urls: List of public image URLs (2-10 images)
            caption: Post caption
            location_id: Optional location ID

        Returns:
            Dict with media_id and permalink
        """
        if len(image_urls) < 2 or len(image_urls) > 10:
            raise ValueError("Carousel must have 2-10 images")

        client = await self._get_client()

        # Step 1: Create individual media containers for each image
        children_ids = []
        for image_url in image_urls:
            container_response = await client.post(
                f"{INSTAGRAM_GRAPH_URL}/{instagram_user_id}/media",
                data={
                    "image_url": image_url,
                    "is_carousel_item": "true",
                    "access_token": access_token
                }
            )
            container_response.raise_for_status()
            children_ids.append(container_response.json()["id"])

        # Wait for all containers to be ready
        for container_id in children_ids:
            await self._wait_for_container(access_token, container_id)

        # Step 2: Create carousel container
        carousel_data = {
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption,
            "access_token": access_token
        }

        if location_id:
            carousel_data["location_id"] = location_id

        carousel_response = await client.post(
            f"{INSTAGRAM_GRAPH_URL}/{instagram_user_id}/media",
            data=carousel_data
        )
        carousel_response.raise_for_status()
        carousel_id = carousel_response.json()["id"]

        # Wait for carousel to be ready
        await self._wait_for_container(access_token, carousel_id)

        # Step 3: Publish carousel
        publish_response = await client.post(
            f"{INSTAGRAM_GRAPH_URL}/{instagram_user_id}/media_publish",
            data={
                "creation_id": carousel_id,
                "access_token": access_token
            }
        )
        publish_response.raise_for_status()
        published = publish_response.json()

        # Get media details
        media_details = await self.get_media_details(access_token, published["id"])

        return {
            "media_id": published["id"],
            "permalink": media_details.get("permalink"),
            "timestamp": media_details.get("timestamp"),
            "media_type": "CAROUSEL",
            "children_count": len(image_urls),
            "status": "published"
        }

    async def _wait_for_container(
        self,
        access_token: str,
        container_id: str,
        *,
        max_attempts: int = 10,
        delay_seconds: int = 2
    ):
        """Wait for a media container to finish processing."""
        import asyncio
        client = await self._get_client()

        for attempt in range(max_attempts):
            response = await client.get(
                f"{INSTAGRAM_GRAPH_URL}/{container_id}",
                params={
                    "fields": "status_code",
                    "access_token": access_token
                }
            )
            response.raise_for_status()
            status = response.json().get("status_code")

            if status == "FINISHED":
                return
            elif status == "ERROR":
                raise RuntimeError(f"Container {container_id} failed processing")

            await asyncio.sleep(delay_seconds)

        raise TimeoutError(f"Container {container_id} processing timed out")

    async def get_media_details(
        self,
        access_token: str,
        media_id: str
    ) -> Dict[str, Any]:
        """Get details about a published media item."""
        client = await self._get_client()

        params = {
            "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username,like_count,comments_count",
            "access_token": access_token
        }

        response = await client.get(
            f"{INSTAGRAM_GRAPH_URL}/{media_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def get_insights(
        self,
        access_token: str,
        media_id: str,
        *,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch engagement metrics for a media item.

        Args:
            access_token: User's access token
            media_id: Instagram media ID
            metrics: Specific metrics to fetch

        Returns:
            Dict with engagement metrics
        """
        client = await self._get_client()

        if metrics is None:
            # Default metrics for image/carousel posts
            metrics = ["engagement", "impressions", "reach", "saved"]

        params = {
            "metric": ",".join(metrics),
            "access_token": access_token
        }

        response = await client.get(
            f"{INSTAGRAM_GRAPH_URL}/{media_id}/insights",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        # Transform to simpler format
        insights = {}
        for item in data.get("data", []):
            insights[item["name"]] = item["values"][0]["value"]

        return {
            "media_id": media_id,
            "metrics": insights,
            "fetched_at": datetime.utcnow().isoformat()
        }

    async def get_account_insights(
        self,
        access_token: str,
        instagram_user_id: str,
        *,
        period: str = "day",
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get account-level insights.

        Args:
            access_token: User's access token
            instagram_user_id: Instagram user ID
            period: Time period (day, week, days_28, lifetime)
            metrics: Specific metrics

        Returns:
            Account insights data
        """
        client = await self._get_client()

        if metrics is None:
            metrics = ["impressions", "reach", "profile_views", "follower_count"]

        params = {
            "metric": ",".join(metrics),
            "period": period,
            "access_token": access_token
        }

        response = await client.get(
            f"{INSTAGRAM_GRAPH_URL}/{instagram_user_id}/insights",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        insights = {}
        for item in data.get("data", []):
            insights[item["name"]] = item["values"][0]["value"] if item.get("values") else None

        return {
            "user_id": instagram_user_id,
            "period": period,
            "metrics": insights,
            "fetched_at": datetime.utcnow().isoformat()
        }

    async def get_recent_media(
        self,
        access_token: str,
        instagram_user_id: str,
        *,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Get user's recent media posts."""
        client = await self._get_client()

        params = {
            "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,like_count,comments_count",
            "limit": limit,
            "access_token": access_token
        }

        response = await client.get(
            f"{INSTAGRAM_GRAPH_URL}/{instagram_user_id}/media",
            params=params
        )
        response.raise_for_status()
        return response.json().get("data", [])

    async def disconnect(self, access_token: str) -> bool:
        """
        Revoke access token (disconnect account).
        Note: This is a best-effort operation.
        """
        # Instagram doesn't have a direct revoke endpoint
        # The token will expire naturally
        # We just need to delete it from our database
        logger.info("Instagram disconnect requested - token will be removed from database")
        return True


# Singleton instance
instagram_service = InstagramService()
