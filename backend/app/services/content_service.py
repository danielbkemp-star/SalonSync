"""
Content Service - AI-powered content generation for social media
KEY DIFFERENTIATOR: Professional caption generation using Claude
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

import anthropic

from app.app_settings import settings
from app.models import MediaSet, SocialPost, Salon

logger = logging.getLogger(__name__)


class ContentService:
    """
    AI-powered content generation service.
    Uses Claude for generating engaging social media captions.
    """

    def __init__(self):
        self._client: Optional[anthropic.Anthropic] = None
        self._configure()

    def _configure(self):
        """Configure Anthropic client"""
        if settings.ANTHROPIC_API_KEY:
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            logger.warning("Anthropic API key not configured - content generation disabled")

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    async def generate_caption(
        self,
        media_set: MediaSet,
        style: str = "professional",
        *,
        salon_name: Optional[str] = None,
        stylist_name: Optional[str] = None,
        custom_instructions: Optional[str] = None,
        include_cta: bool = True,
        max_length: int = 2200
    ) -> Dict[str, Any]:
        """
        Generate an engaging Instagram caption for a hair transformation.

        Args:
            media_set: The MediaSet containing transformation details
            style: Tone of the caption (professional, playful, luxurious, educational)
            salon_name: Salon name to mention
            stylist_name: Stylist name to credit
            custom_instructions: Additional instructions for the AI
            include_cta: Whether to include a call-to-action
            max_length: Maximum caption length (Instagram limit is 2200)

        Returns:
            Dict with caption, hashtags, alt_captions, and metadata
        """
        if not self._client:
            raise RuntimeError("Content service not configured - missing Anthropic API key")

        # Extract details from media_set
        services = media_set.services_performed or []
        techniques = media_set.techniques_used or []
        products = media_set.products_used or []
        tags = media_set.tags or []

        # Build product names list
        product_names = []
        if products:
            for p in products:
                if isinstance(p, dict) and p.get('name'):
                    product_names.append(p['name'])
                elif isinstance(p, str):
                    product_names.append(p)

        # Build the prompt
        prompt = self._build_caption_prompt(
            services=services,
            techniques=techniques,
            products=product_names,
            tags=tags,
            style=style,
            salon_name=salon_name,
            stylist_name=stylist_name,
            custom_instructions=custom_instructions,
            include_cta=include_cta,
            max_length=max_length
        )

        try:
            message = self._client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text.strip()

            # Parse JSON response
            result = self._parse_caption_response(response_text)

            # Add metadata
            result["model"] = "claude-3-haiku-20240307"
            result["generated_at"] = datetime.utcnow().isoformat()
            result["style"] = style
            result["media_set_id"] = media_set.id

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse caption JSON: {e}")
            # Return raw text as fallback
            return {
                "caption": response_text,
                "hashtags": await self.generate_hashtags(services, tags),
                "alt_captions": [],
                "model": "claude-3-haiku-20240307",
                "generated_at": datetime.utcnow().isoformat(),
                "style": style,
                "parse_error": str(e)
            }
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            raise

    def _build_caption_prompt(
        self,
        *,
        services: List[str],
        techniques: List[str],
        products: List[str],
        tags: List[str],
        style: str,
        salon_name: Optional[str],
        stylist_name: Optional[str],
        custom_instructions: Optional[str],
        include_cta: bool,
        max_length: int
    ) -> str:
        """Build the caption generation prompt"""

        style_descriptions = {
            "professional": "professional, elegant, and sophisticated - perfect for high-end salons",
            "playful": "fun, energetic, and relatable with natural emoji usage",
            "luxurious": "exclusive, refined, and aspirational - emphasize the premium experience",
            "educational": "informative and helpful - share tips and insights about the techniques used"
        }

        style_desc = style_descriptions.get(style, style_descriptions["professional"])

        prompt = f"""You are a social media expert for a high-end hair salon.

Generate an engaging Instagram caption for this hair transformation:

**Services:** {', '.join(services) if services else 'Hair transformation'}
**Techniques:** {', '.join(techniques) if techniques else 'Not specified'}
**Products:** {', '.join(products) if products else 'Not specified'}
**Style tags:** {', '.join(tags) if tags else 'Not specified'}

**Tone:** {style} - {style_desc}

**Requirements:**
- Under {max_length} characters total
- Use emojis naturally (not excessively) - 2-4 emojis max
- Be authentic, not salesy
- Focus on the transformation story and results
- Make readers feel inspired"""

        if include_cta:
            prompt += "\n- Include a subtle call-to-action (book now, link in bio, DM us, etc.)"

        if salon_name:
            prompt += f"\n- Salon name: {salon_name}"

        if stylist_name:
            prompt += f"\n- Stylist: {stylist_name} (credit them naturally)"

        if custom_instructions:
            prompt += f"\n\n**Additional instructions:**\n{custom_instructions}"

        prompt += """

**Return ONLY valid JSON in this exact format:**
{
  "caption": "The main caption text (100-300 characters ideal)",
  "hashtags": ["transformation", "balayage", "hairgoals", "...15-20 relevant hashtags"],
  "alt_captions": ["Alternative caption 1", "Alternative caption 2"]
}

Do not include any text before or after the JSON."""

        return prompt

    def _parse_caption_response(self, response: str) -> Dict[str, Any]:
        """Parse the JSON response from Claude"""
        # Clean up the response
        response = response.strip()

        # Handle markdown code blocks
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        # Parse JSON
        data = json.loads(response)

        return {
            "caption": data.get("caption", ""),
            "hashtags": data.get("hashtags", []),
            "alt_captions": data.get("alt_captions", [])
        }

    async def generate_hashtags(
        self,
        services: List[str],
        tags: List[str],
        *,
        location: Optional[str] = None,
        count: int = 20
    ) -> List[str]:
        """
        Generate optimized hashtag set for maximum reach.

        Args:
            services: Services performed
            tags: Style tags
            location: Optional location for local hashtags
            count: Number of hashtags to generate

        Returns:
            List of hashtags (without # prefix)
        """
        # Base hashtags (high reach)
        base_hashtags = [
            "hairtransformation",
            "hairgoals",
            "hairstylist",
            "salonlife",
            "hairinspo",
            "hairofinstagram",
            "behindthechair"
        ]

        # Service-specific hashtags
        service_hashtags = []
        service_map = {
            "balayage": ["balayage", "balayagehair", "balayageombre", "handpaintedhair"],
            "highlights": ["highlights", "highlightshair", "babylights", "dimensionalhair"],
            "color": ["haircolor", "haircolorist", "colorspecialist", "hairpainting"],
            "cut": ["haircut", "haircutstyle", "freshcut", "newhaircut"],
            "blonde": ["blondehair", "blondebalayage", "blondespecialist", "iceblonde"],
            "brunette": ["brunettehair", "brunettbalayage", "brownhair", "richbrunette"],
            "red": ["redhair", "redhead", "copperhair", "auburnhair"],
            "extensions": ["hairextensions", "extensionspecialist", "lengthcheck"],
            "keratin": ["keratintreatment", "smoothhair", "frizzfree"],
            "bridal": ["bridalhair", "weddinghair", "bridalhairstylist"],
        }

        for service in services:
            service_lower = service.lower()
            for key, hashtags in service_map.items():
                if key in service_lower:
                    service_hashtags.extend(hashtags)

            # Add the service name as hashtag
            clean_service = service_lower.replace(" ", "").replace("-", "")
            if clean_service and clean_service not in service_hashtags:
                service_hashtags.append(clean_service)

        # Tag-based hashtags
        tag_hashtags = []
        for tag in tags:
            clean_tag = tag.lower().replace(" ", "").replace("#", "").replace("-", "")
            if clean_tag:
                tag_hashtags.append(clean_tag)

        # Location hashtags
        location_hashtags = []
        if location:
            clean_location = location.lower().replace(" ", "").replace(",", "")
            location_hashtags.extend([
                f"{clean_location}hair",
                f"{clean_location}salon",
                f"{clean_location}hairstylist"
            ])

        # Combine all hashtags
        all_hashtags = base_hashtags + service_hashtags + tag_hashtags + location_hashtags

        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for h in all_hashtags:
            h_clean = h.strip().lower()
            if h_clean and h_clean not in seen and len(h_clean) <= 30:
                seen.add(h_clean)
                unique_hashtags.append(h_clean)

        return unique_hashtags[:count]

    async def suggest_best_time(
        self,
        salon_id: int,
        platform: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Analyze past engagement to suggest optimal posting time.

        Args:
            salon_id: Salon ID
            platform: Target platform (instagram, tiktok)
            db: Database session

        Returns:
            Dict with suggested times and reasoning
        """
        # Get past posts with engagement data
        posts = db.query(SocialPost).filter(
            SocialPost.salon_id == salon_id,
            SocialPost.platform == platform,
            SocialPost.published_at.isnot(None),
            SocialPost.engagement_rate.isnot(None)
        ).order_by(SocialPost.engagement_rate.desc()).limit(50).all()

        if len(posts) >= 10:
            # Analyze actual engagement data
            hour_engagement = {}
            day_engagement = {}

            for post in posts:
                hour = post.published_at.hour
                day = post.published_at.strftime("%A")
                rate = post.engagement_rate or 0

                if hour not in hour_engagement:
                    hour_engagement[hour] = []
                hour_engagement[hour].append(rate)

                if day not in day_engagement:
                    day_engagement[day] = []
                day_engagement[day].append(rate)

            # Calculate averages
            best_hours = sorted(
                hour_engagement.items(),
                key=lambda x: sum(x[1]) / len(x[1]),
                reverse=True
            )[:4]

            best_days = sorted(
                day_engagement.items(),
                key=lambda x: sum(x[1]) / len(x[1]),
                reverse=True
            )[:3]

            return {
                "platform": platform,
                "best_hours": [h[0] for h in best_hours],
                "best_days": [d[0] for d in best_days],
                "data_source": "analytics",
                "sample_size": len(posts),
                "note": f"Based on {len(posts)} posts with engagement data"
            }
        else:
            # Fall back to industry best practices
            best_times = {
                "instagram": {
                    "hours": [9, 11, 14, 19],
                    "days": ["Tuesday", "Wednesday", "Thursday"]
                },
                "tiktok": {
                    "hours": [7, 12, 15, 19, 21],
                    "days": ["Tuesday", "Thursday", "Friday"]
                },
                "facebook": {
                    "hours": [9, 13, 16],
                    "days": ["Wednesday", "Thursday", "Friday"]
                }
            }

            platform_data = best_times.get(platform, best_times["instagram"])

            return {
                "platform": platform,
                "best_hours": platform_data["hours"],
                "best_days": platform_data["days"],
                "data_source": "industry_best_practices",
                "sample_size": 0,
                "note": "Not enough data yet. These are industry best practices for salons."
            }

    async def generate_content_calendar(
        self,
        salon_id: int,
        db: Session,
        *,
        days: int = 7,
        posts_per_day: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Generate a content calendar suggestion.

        Args:
            salon_id: Salon ID
            db: Database session
            days: Number of days to plan
            posts_per_day: Target posts per day

        Returns:
            List of suggested posting slots
        """
        # Get best times
        instagram_times = await self.suggest_best_time(salon_id, "instagram", db)

        calendar = []
        today = datetime.utcnow().date()

        for day_offset in range(days):
            post_date = today + timedelta(days=day_offset)
            day_name = post_date.strftime("%A")

            # Check if this is a good day
            is_best_day = day_name in instagram_times["best_days"]

            for i in range(posts_per_day):
                # Pick a posting hour
                hour_index = i % len(instagram_times["best_hours"])
                post_hour = instagram_times["best_hours"][hour_index]

                post_datetime = datetime.combine(
                    post_date,
                    datetime.min.time().replace(hour=post_hour)
                )

                calendar.append({
                    "date": post_date.isoformat(),
                    "datetime": post_datetime.isoformat(),
                    "day": day_name,
                    "hour": post_hour,
                    "is_optimal_day": is_best_day,
                    "slot_number": i + 1,
                    "suggestion": self._get_content_suggestion(day_name, i)
                })

        return calendar

    def _get_content_suggestion(self, day: str, slot: int) -> str:
        """Get content type suggestion based on day and slot"""
        suggestions = {
            "Monday": ["Transformation reveal", "Week ahead goals"],
            "Tuesday": ["Before/after", "Technique spotlight"],
            "Wednesday": ["Behind the scenes", "Product feature"],
            "Thursday": ["Client appreciation", "Throwback transformation"],
            "Friday": ["Weekend ready looks", "Stylist spotlight"],
            "Saturday": ["Salon vibes", "Team at work"],
            "Sunday": ["Self-care tips", "Inspiration quote"]
        }

        day_suggestions = suggestions.get(day, ["Transformation"])
        return day_suggestions[slot % len(day_suggestions)]


# Singleton instance
content_service = ContentService()
