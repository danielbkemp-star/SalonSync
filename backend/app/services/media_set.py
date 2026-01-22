"""
MediaSet service - The Formula Vault
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import MediaSet, Client, Staff
from app.schemas.media_set import MediaSetCreate, MediaSetUpdate, MediaSetSearch
from app.services.base import BaseService
from app.services.cloudinary import cloudinary_service
from app.services.ai_caption import ai_caption_service


class MediaSetService(BaseService[MediaSet, MediaSetCreate, MediaSetUpdate]):
    """Service for MediaSet operations - The Formula Vault"""

    def __init__(self):
        super().__init__(MediaSet)

    async def create_with_photos(
        self,
        db: AsyncSession,
        *,
        obj_in: MediaSetCreate,
        before_photo_data: Optional[bytes] = None,
        after_photo_data: Optional[bytes] = None
    ) -> MediaSet:
        """Create a media set with optional photo uploads"""
        data = obj_in.model_dump(exclude_unset=True)

        # Upload photos to Cloudinary if provided
        if before_photo_data and after_photo_data and cloudinary_service.is_configured:
            before_result, after_result = await cloudinary_service.upload_before_after(
                before_photo_data,
                after_photo_data,
                salon_id=data['salon_id'],
                staff_id=data['staff_id']
            )
            data['before_photo_url'] = before_result['url']
            data['before_photo_public_id'] = before_result['public_id']
            data['after_photo_url'] = after_result['url']
            data['after_photo_public_id'] = after_result['public_id']

        db_obj = MediaSet(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def generate_comparison(
        self,
        db: AsyncSession,
        *,
        media_set: MediaSet,
        layout: str = "side_by_side"
    ) -> MediaSet:
        """Generate a comparison image for a media set"""
        if not media_set.before_photo_url or not media_set.after_photo_url:
            raise ValueError("Both before and after photos are required")

        if not cloudinary_service.is_configured:
            raise RuntimeError("Cloudinary not configured")

        result = await cloudinary_service.create_comparison_image(
            media_set.before_photo_url,
            media_set.after_photo_url,
            layout=layout,
            salon_id=media_set.salon_id,
            media_set_id=media_set.id
        )

        media_set.comparison_photo_url = result['url']
        media_set.comparison_photo_public_id = result['public_id']

        db.add(media_set)
        await db.commit()
        await db.refresh(media_set)
        return media_set

    async def generate_ai_caption(
        self,
        db: AsyncSession,
        *,
        media_set: MediaSet,
        tone: str = "professional",
        include_hashtags: bool = True,
        hashtag_count: int = 15,
        custom_instructions: Optional[str] = None,
        salon_name: Optional[str] = None,
        stylist_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI caption for a media set"""
        if not ai_caption_service.is_configured:
            raise RuntimeError("AI service not configured")

        result = await ai_caption_service.generate_caption(
            services_performed=media_set.services_performed or [],
            techniques_used=media_set.techniques_used or [],
            color_formulas=media_set.color_formulas,
            starting_level=media_set.starting_level,
            achieved_level=media_set.achieved_level,
            tags=media_set.tags,
            tone=tone,
            include_hashtags=include_hashtags,
            hashtag_count=hashtag_count,
            mention_products=True,
            products_used=media_set.products_used,
            custom_instructions=custom_instructions,
            salon_name=salon_name,
            stylist_name=stylist_name
        )

        # Save generated caption to media set
        media_set.ai_generated_caption = result['caption']
        media_set.suggested_hashtags = result['hashtags']

        db.add(media_set)
        await db.commit()
        await db.refresh(media_set)

        return result

    async def search(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        search: MediaSetSearch,
        skip: int = 0,
        limit: int = 20
    ) -> List[MediaSet]:
        """Search media sets with various filters"""
        query = select(MediaSet).where(MediaSet.salon_id == salon_id)

        if search.staff_id:
            query = query.where(MediaSet.staff_id == search.staff_id)

        if search.client_id:
            query = query.where(MediaSet.client_id == search.client_id)

        if search.is_portfolio_piece is not None:
            query = query.where(MediaSet.is_portfolio_piece == search.is_portfolio_piece)

        if search.has_before_after:
            query = query.where(
                and_(
                    MediaSet.before_photo_url.isnot(None),
                    MediaSet.after_photo_url.isnot(None)
                )
            )

        if search.can_post_to_social:
            query = query.where(
                and_(
                    MediaSet.client_social_consent == True,
                    MediaSet.is_private == False,
                    MediaSet.before_photo_url.isnot(None),
                    MediaSet.after_photo_url.isnot(None)
                )
            )

        if search.tags:
            # Filter by any matching tag (uses JSONB contains)
            for tag in search.tags:
                query = query.where(MediaSet.tags.contains([tag]))

        if search.techniques:
            for technique in search.techniques:
                query = query.where(MediaSet.techniques_used.contains([technique]))

        if search.date_from:
            query = query.where(MediaSet.service_date >= search.date_from)

        if search.date_to:
            query = query.where(MediaSet.service_date <= search.date_to)

        query = query.order_by(MediaSet.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_portfolio(
        self,
        db: AsyncSession,
        salon_id: int,
        *,
        staff_id: Optional[int] = None,
        limit: int = 20
    ) -> List[MediaSet]:
        """Get portfolio pieces for display"""
        query = select(MediaSet).where(
            and_(
                MediaSet.salon_id == salon_id,
                MediaSet.is_portfolio_piece == True,
                MediaSet.is_private == False,
                MediaSet.before_photo_url.isnot(None),
                MediaSet.after_photo_url.isnot(None)
            )
        )

        if staff_id:
            query = query.where(MediaSet.staff_id == staff_id)

        query = query.order_by(MediaSet.created_at.desc())
        query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_client_history(
        self,
        db: AsyncSession,
        client_id: int
    ) -> List[MediaSet]:
        """Get all media sets for a client (service history with formulas)"""
        query = select(MediaSet).where(
            MediaSet.client_id == client_id
        ).order_by(MediaSet.service_date.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_formula_history(
        self,
        db: AsyncSession,
        client_id: int
    ) -> List[Dict[str, Any]]:
        """Get color formula history for a client"""
        media_sets = await self.get_client_history(db, client_id)

        formulas = []
        for ms in media_sets:
            if ms.color_formulas:
                formulas.append({
                    "date": ms.service_date,
                    "formulas": ms.color_formulas,
                    "techniques": ms.techniques_used,
                    "starting_level": ms.starting_level,
                    "achieved_level": ms.achieved_level,
                    "notes": ms.stylist_notes,
                    "media_set_id": ms.id
                })

        return formulas

    async def copy_formula(
        self,
        db: AsyncSession,
        *,
        source_media_set_id: int,
        new_media_set: MediaSetCreate
    ) -> MediaSet:
        """Copy formula from one media set to a new one"""
        source = await self.get(db, source_media_set_id)
        if not source:
            raise ValueError("Source media set not found")

        # Copy formula-related fields
        data = new_media_set.model_dump(exclude_unset=True)
        data['color_formulas'] = source.color_formulas
        data['products_used'] = source.products_used
        data['techniques_used'] = source.techniques_used

        db_obj = MediaSet(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete_with_photos(
        self,
        db: AsyncSession,
        *,
        media_set: MediaSet
    ) -> bool:
        """Delete a media set and its associated photos from Cloudinary"""
        # Delete photos from Cloudinary
        if cloudinary_service.is_configured:
            if media_set.before_photo_public_id:
                await cloudinary_service.delete_image(media_set.before_photo_public_id)
            if media_set.after_photo_public_id:
                await cloudinary_service.delete_image(media_set.after_photo_public_id)
            if media_set.comparison_photo_public_id:
                await cloudinary_service.delete_image(media_set.comparison_photo_public_id)

            # Delete additional photos
            for photo in media_set.additional_photos or []:
                if photo.get('public_id'):
                    await cloudinary_service.delete_image(photo['public_id'])

        # Delete from database
        await db.delete(media_set)
        await db.commit()
        return True


# Singleton instance
media_set_service = MediaSetService()
