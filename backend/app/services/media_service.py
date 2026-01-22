"""
Media Service - Photo upload and platform optimization
Wraps CloudinaryService with salon-specific features
"""

import logging
from typing import Optional, Dict, Any, List
from io import BytesIO

from app.services.cloudinary import cloudinary_service
from app.app_settings import settings

logger = logging.getLogger(__name__)


# Platform dimensions for social media
PLATFORM_SPECS = {
    "instagram_square": {"width": 1080, "height": 1080, "aspect": "1:1"},
    "instagram_portrait": {"width": 1080, "height": 1350, "aspect": "4:5"},
    "instagram_story": {"width": 1080, "height": 1920, "aspect": "9:16"},
    "tiktok": {"width": 1080, "height": 1920, "aspect": "9:16"},
    "facebook": {"width": 1200, "height": 630, "aspect": "1.91:1"},
    "twitter": {"width": 1200, "height": 675, "aspect": "16:9"},
    "thumbnail": {"width": 400, "height": 400, "aspect": "1:1"},
}


class MediaService:
    """
    High-level media service for SalonSync.
    Handles photo uploads, comparisons, and platform optimization.
    """

    def __init__(self):
        self._cloudinary = cloudinary_service

    @property
    def is_configured(self) -> bool:
        return self._cloudinary.is_configured

    async def upload_photo(
        self,
        file_data: bytes,
        folder: str,
        *,
        salon_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        optimize: bool = True
    ) -> Dict[str, Any]:
        """
        Upload a photo to Cloudinary with optimization.

        Args:
            file_data: Raw image bytes
            folder: Folder path (e.g., "before_after", "products")
            salon_id: Optional salon ID for folder organization
            tags: Optional tags for organization
            optimize: Whether to apply automatic optimization

        Returns:
            Dict with url, public_id, dimensions, etc.
        """
        if not self._cloudinary.is_configured:
            raise RuntimeError("Media service not configured - missing Cloudinary credentials")

        # Build folder path
        if salon_id:
            full_folder = f"salonsync/salon_{salon_id}/{folder}"
        else:
            full_folder = f"salonsync/{folder}"

        # Build tags
        all_tags = tags or []
        if salon_id:
            all_tags.append(f"salon_{salon_id}")

        # Default transformations for optimization
        transformation = None
        if optimize:
            transformation = [
                {"quality": "auto:good"},
                {"fetch_format": "auto"}
            ]

        result = await self._cloudinary.upload_image(
            file_data,
            folder=full_folder,
            tags=all_tags,
            transformation=transformation
        )

        return {
            "url": result["url"],
            "public_id": result["public_id"],
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format"),
            "size_bytes": result.get("bytes"),
        }

    async def upload_before_after(
        self,
        before_data: bytes,
        after_data: bytes,
        *,
        salon_id: int,
        staff_id: int,
        client_id: Optional[int] = None,
        media_set_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Upload a before/after photo pair.

        Returns:
            Dict with before_url, after_url, and metadata
        """
        before_result, after_result = await self._cloudinary.upload_before_after(
            before_data,
            after_data,
            salon_id=salon_id,
            staff_id=staff_id,
            media_set_id=media_set_id
        )

        return {
            "before": {
                "url": before_result["url"],
                "public_id": before_result["public_id"],
                "width": before_result.get("width"),
                "height": before_result.get("height"),
            },
            "after": {
                "url": after_result["url"],
                "public_id": after_result["public_id"],
                "width": after_result.get("width"),
                "height": after_result.get("height"),
            },
            "salon_id": salon_id,
            "staff_id": staff_id,
            "client_id": client_id,
        }

    async def create_comparison(
        self,
        before_url: str,
        after_url: str,
        *,
        salon_id: int,
        media_set_id: int,
        layout: str = "side_by_side",
        add_labels: bool = True
    ) -> str:
        """
        Generate a side-by-side or top-bottom comparison image.

        Args:
            before_url: URL of before image
            after_url: URL of after image
            salon_id: Salon ID
            media_set_id: Media set ID
            layout: "side_by_side" or "top_bottom"
            add_labels: Whether to add "Before" / "After" labels

        Returns:
            URL of the generated comparison image
        """
        result = await self._cloudinary.create_comparison_image(
            before_url,
            after_url,
            layout=layout,
            salon_id=salon_id,
            media_set_id=media_set_id
        )

        return result["url"]

    async def optimize_for_platform(
        self,
        source_url: str,
        platform: str,
        *,
        crop: str = "fill",
        gravity: str = "auto"
    ) -> str:
        """
        Resize and optimize an image for a specific social media platform.

        Args:
            source_url: Original image URL
            platform: Target platform (instagram_square, instagram_story, tiktok, etc.)
            crop: Crop mode (fill, fit, limit, etc.)
            gravity: Focus point (auto, face, center, etc.)

        Returns:
            Optimized image URL
        """
        if platform not in PLATFORM_SPECS:
            raise ValueError(f"Unknown platform: {platform}. Available: {list(PLATFORM_SPECS.keys())}")

        specs = PLATFORM_SPECS[platform]

        # Extract public_id from URL
        public_id = self._cloudinary._extract_public_id(source_url)

        # Generate optimized URL
        import cloudinary
        optimized_url = cloudinary.CloudinaryImage(public_id).build_url(
            transformation=[
                {
                    "width": specs["width"],
                    "height": specs["height"],
                    "crop": crop,
                    "gravity": gravity
                },
                {"quality": "auto:good"},
                {"fetch_format": "auto"}
            ],
            secure=True
        )

        return optimized_url

    async def get_platform_variants(
        self,
        source_url: str,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Generate URLs for multiple platform sizes from a single source.

        Args:
            source_url: Original image URL
            platforms: List of platforms (defaults to all)

        Returns:
            Dict mapping platform name to optimized URL
        """
        if platforms is None:
            platforms = ["instagram_square", "instagram_story", "tiktok", "thumbnail"]

        variants = {}
        for platform in platforms:
            try:
                variants[platform] = await self.optimize_for_platform(source_url, platform)
            except Exception as e:
                logger.warning(f"Failed to generate {platform} variant: {e}")

        return variants

    async def delete_photo(self, public_id: str) -> bool:
        """Delete a photo from storage."""
        return await self._cloudinary.delete_image(public_id)

    async def delete_media_set_photos(
        self,
        salon_id: int,
        staff_id: int,
        media_set_id: int
    ) -> bool:
        """Delete all photos associated with a media set."""
        folder = f"salonsync/salon_{salon_id}/staff_{staff_id}"
        # Delete specific media set photos
        try:
            import cloudinary.api
            prefix = f"{folder}/media_{media_set_id}"
            cloudinary.api.delete_resources_by_prefix(prefix)
            return True
        except Exception as e:
            logger.error(f"Failed to delete media set photos: {e}")
            return False

    def get_thumbnail_url(self, source_url: str, size: int = 200) -> str:
        """Get a square thumbnail URL."""
        public_id = self._cloudinary._extract_public_id(source_url)
        return self._cloudinary.get_thumbnail_url(public_id, size)

    def get_responsive_urls(
        self,
        source_url: str,
        widths: Optional[List[int]] = None
    ) -> Dict[int, str]:
        """
        Generate responsive image URLs for different screen sizes.

        Args:
            source_url: Original image URL
            widths: List of widths (defaults to common breakpoints)

        Returns:
            Dict mapping width to URL
        """
        if widths is None:
            widths = [320, 640, 768, 1024, 1280, 1920]

        public_id = self._cloudinary._extract_public_id(source_url)
        urls = {}

        for width in widths:
            urls[width] = self._cloudinary.get_optimized_url(
                public_id,
                width=width,
                quality="auto:eco"
            )

        return urls


# Singleton instance
media_service = MediaService()
