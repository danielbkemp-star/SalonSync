"""
Cloudinary service - Image upload and management
"""

import logging
from typing import Optional, Dict, Any, Tuple
from io import BytesIO

import cloudinary
import cloudinary.uploader
import cloudinary.api
from PIL import Image

from app.app_settings import settings

logger = logging.getLogger(__name__)


class CloudinaryService:
    """Service for Cloudinary image operations"""

    def __init__(self):
        self._configured = False
        self._configure()

    def _configure(self):
        """Configure Cloudinary with credentials"""
        if (
            settings.CLOUDINARY_CLOUD_NAME and
            settings.CLOUDINARY_API_KEY and
            settings.CLOUDINARY_API_SECRET
        ):
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True
            )
            self._configured = True
        else:
            logger.warning("Cloudinary credentials not configured")

    @property
    def is_configured(self) -> bool:
        return self._configured

    async def upload_image(
        self,
        file_data: bytes,
        *,
        folder: str = "salonsync",
        public_id: Optional[str] = None,
        transformation: Optional[Dict] = None,
        tags: Optional[list] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Upload an image to Cloudinary.

        Args:
            file_data: Raw image bytes
            folder: Cloudinary folder path
            public_id: Custom public ID (auto-generated if not provided)
            transformation: Upload-time transformations
            tags: Tags for organization
            context: Additional metadata

        Returns:
            Cloudinary upload response with url, public_id, etc.
        """
        if not self._configured:
            raise RuntimeError("Cloudinary not configured")

        upload_options = {
            "folder": folder,
            "resource_type": "image",
            "overwrite": True,
        }

        if public_id:
            upload_options["public_id"] = public_id

        if transformation:
            upload_options["transformation"] = transformation

        if tags:
            upload_options["tags"] = tags

        if context:
            upload_options["context"] = context

        # Default transformations for salon photos
        upload_options.setdefault("transformation", [
            {"quality": "auto:good"},
            {"fetch_format": "auto"}
        ])

        try:
            result = cloudinary.uploader.upload(file_data, **upload_options)
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "width": result.get("width"),
                "height": result.get("height"),
                "format": result.get("format"),
                "bytes": result.get("bytes"),
                "resource_type": result.get("resource_type"),
            }
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            raise

    async def upload_before_after(
        self,
        before_data: bytes,
        after_data: bytes,
        *,
        salon_id: int,
        staff_id: int,
        media_set_id: Optional[int] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Upload before and after photos with consistent naming.

        Returns:
            Tuple of (before_result, after_result)
        """
        folder = f"salonsync/salon_{salon_id}/staff_{staff_id}"
        prefix = f"media_{media_set_id}" if media_set_id else "temp"

        before_result = await self.upload_image(
            before_data,
            folder=folder,
            public_id=f"{prefix}_before",
            tags=["before", f"salon_{salon_id}", f"staff_{staff_id}"]
        )

        after_result = await self.upload_image(
            after_data,
            folder=folder,
            public_id=f"{prefix}_after",
            tags=["after", f"salon_{salon_id}", f"staff_{staff_id}"]
        )

        return before_result, after_result

    async def create_comparison_image(
        self,
        before_url: str,
        after_url: str,
        *,
        layout: str = "side_by_side",
        salon_id: int,
        media_set_id: int
    ) -> Dict[str, Any]:
        """
        Create a side-by-side comparison image using Cloudinary transformations.

        Args:
            before_url: URL of before image
            after_url: URL of after image
            layout: "side_by_side" or "top_bottom"
            salon_id: Salon ID for folder organization
            media_set_id: Media set ID for naming

        Returns:
            Cloudinary result with comparison image URL
        """
        if not self._configured:
            raise RuntimeError("Cloudinary not configured")

        # Extract public IDs from URLs
        before_public_id = self._extract_public_id(before_url)
        after_public_id = self._extract_public_id(after_url)

        if layout == "side_by_side":
            # Create side-by-side using overlay
            transformation = [
                {"width": 600, "height": 800, "crop": "fill", "gravity": "face"},
                {
                    "overlay": after_public_id.replace("/", ":"),
                    "width": 600,
                    "height": 800,
                    "crop": "fill",
                    "gravity": "face",
                    "x": 600,
                    "flags": "layer_apply"
                },
                {"width": 1200}
            ]
        else:  # top_bottom
            transformation = [
                {"width": 800, "height": 600, "crop": "fill", "gravity": "face"},
                {
                    "overlay": after_public_id.replace("/", ":"),
                    "width": 800,
                    "height": 600,
                    "crop": "fill",
                    "gravity": "face",
                    "y": 600,
                    "flags": "layer_apply"
                },
                {"height": 1200}
            ]

        folder = f"salonsync/salon_{salon_id}/comparisons"

        try:
            result = cloudinary.uploader.upload(
                before_url,
                folder=folder,
                public_id=f"comparison_{media_set_id}",
                transformation=transformation,
                tags=["comparison", f"salon_{salon_id}", f"media_set_{media_set_id}"]
            )
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "width": result.get("width"),
                "height": result.get("height"),
            }
        except Exception as e:
            logger.error(f"Failed to create comparison image: {e}")
            raise

    async def delete_image(self, public_id: str) -> bool:
        """Delete an image from Cloudinary"""
        if not self._configured:
            raise RuntimeError("Cloudinary not configured")

        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get("result") == "ok"
        except Exception as e:
            logger.error(f"Failed to delete image {public_id}: {e}")
            return False

    async def delete_folder(self, folder: str) -> bool:
        """Delete all images in a folder"""
        if not self._configured:
            raise RuntimeError("Cloudinary not configured")

        try:
            # Delete all resources in folder
            cloudinary.api.delete_resources_by_prefix(folder)
            # Delete the empty folder
            cloudinary.api.delete_folder(folder)
            return True
        except Exception as e:
            logger.error(f"Failed to delete folder {folder}: {e}")
            return False

    def get_optimized_url(
        self,
        public_id: str,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: str = "fill",
        quality: str = "auto:good",
        format: str = "auto"
    ) -> str:
        """Get an optimized URL for an image"""
        transformations = [
            {"quality": quality},
            {"fetch_format": format}
        ]

        if width or height:
            size_transform = {"crop": crop}
            if width:
                size_transform["width"] = width
            if height:
                size_transform["height"] = height
            transformations.insert(0, size_transform)

        return cloudinary.CloudinaryImage(public_id).build_url(
            transformation=transformations,
            secure=True
        )

    def get_thumbnail_url(self, public_id: str, size: int = 200) -> str:
        """Get a square thumbnail URL"""
        return self.get_optimized_url(
            public_id,
            width=size,
            height=size,
            crop="thumb",
            quality="auto:low"
        )

    def _extract_public_id(self, url: str) -> str:
        """Extract public_id from Cloudinary URL"""
        # URL format: https://res.cloudinary.com/{cloud}/image/upload/v{version}/{public_id}.{format}
        try:
            parts = url.split("/upload/")
            if len(parts) > 1:
                path = parts[1]
                # Remove version if present
                if path.startswith("v"):
                    path = "/".join(path.split("/")[1:])
                # Remove file extension
                if "." in path:
                    path = path.rsplit(".", 1)[0]
                return path
        except Exception:
            pass
        return url


# Singleton instance
cloudinary_service = CloudinaryService()
