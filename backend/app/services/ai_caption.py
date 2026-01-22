"""
AI Caption Generation Service using Anthropic Claude
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import anthropic

from app.app_settings import settings

logger = logging.getLogger(__name__)


class AICaptionService:
    """Service for AI-generated social media captions"""

    def __init__(self):
        self._client: Optional[anthropic.Anthropic] = None
        self._configure()

    def _configure(self):
        """Configure Anthropic client"""
        if settings.ANTHROPIC_API_KEY:
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            logger.warning("Anthropic API key not configured")

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    async def generate_caption(
        self,
        *,
        services_performed: List[str],
        techniques_used: List[str],
        color_formulas: Optional[List[Dict]] = None,
        starting_level: Optional[str] = None,
        achieved_level: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tone: str = "professional",
        include_hashtags: bool = True,
        hashtag_count: int = 15,
        include_call_to_action: bool = True,
        mention_products: bool = False,
        products_used: Optional[List[Dict]] = None,
        custom_instructions: Optional[str] = None,
        salon_name: Optional[str] = None,
        stylist_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an Instagram caption for a hair transformation.

        Returns:
            Dict with 'caption', 'hashtags', 'full_text'
        """
        if not self._client:
            raise RuntimeError("Anthropic client not configured")

        # Build the prompt
        prompt = self._build_caption_prompt(
            services_performed=services_performed,
            techniques_used=techniques_used,
            color_formulas=color_formulas,
            starting_level=starting_level,
            achieved_level=achieved_level,
            tags=tags,
            tone=tone,
            include_call_to_action=include_call_to_action,
            mention_products=mention_products,
            products_used=products_used,
            custom_instructions=custom_instructions,
            salon_name=salon_name,
            stylist_name=stylist_name
        )

        try:
            message = self._client.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cost-effective for captions
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            caption_text = message.content[0].text.strip()

            # Generate hashtags separately for better control
            hashtags = []
            if include_hashtags:
                hashtags = await self._generate_hashtags(
                    services_performed=services_performed,
                    techniques_used=techniques_used,
                    tags=tags,
                    count=hashtag_count
                )

            return {
                "caption": caption_text,
                "hashtags": hashtags,
                "full_text": self._combine_caption_hashtags(caption_text, hashtags),
                "model": "claude-3-haiku-20240307",
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to generate caption: {e}")
            raise

    def _build_caption_prompt(
        self,
        *,
        services_performed: List[str],
        techniques_used: List[str],
        color_formulas: Optional[List[Dict]],
        starting_level: Optional[str],
        achieved_level: Optional[str],
        tags: Optional[List[str]],
        tone: str,
        include_call_to_action: bool,
        mention_products: bool,
        products_used: Optional[List[Dict]],
        custom_instructions: Optional[str],
        salon_name: Optional[str],
        stylist_name: Optional[str]
    ) -> str:
        """Build the caption generation prompt"""

        tone_descriptions = {
            "professional": "professional, elegant, and sophisticated",
            "casual": "friendly, approachable, and conversational",
            "fun": "playful, energetic, and enthusiastic with emojis",
            "luxurious": "high-end, exclusive, and refined"
        }

        tone_desc = tone_descriptions.get(tone, tone_descriptions["professional"])

        prompt = f"""Write an Instagram caption for a hair transformation photo. The caption should be {tone_desc}.

TRANSFORMATION DETAILS:
- Services: {', '.join(services_performed)}
- Techniques: {', '.join(techniques_used) if techniques_used else 'Not specified'}
"""

        if starting_level and achieved_level:
            prompt += f"- Transformation: From {starting_level} to {achieved_level}\n"

        if color_formulas and mention_products:
            brands = list(set(f.get('brand', '') for f in color_formulas if f.get('brand')))
            if brands:
                prompt += f"- Color brands used: {', '.join(brands)}\n"

        if products_used and mention_products:
            product_names = [p.get('name', '') for p in products_used if p.get('name')]
            if product_names:
                prompt += f"- Products: {', '.join(product_names[:3])}\n"

        if tags:
            prompt += f"- Style tags: {', '.join(tags)}\n"

        if salon_name:
            prompt += f"- Salon: {salon_name}\n"

        if stylist_name:
            prompt += f"- Stylist: {stylist_name}\n"

        prompt += """
REQUIREMENTS:
- Keep the caption between 100-200 characters (short and impactful)
- Focus on the transformation and results
- Do NOT include hashtags (those will be added separately)
"""

        if include_call_to_action:
            prompt += "- End with a subtle call to action (book now, link in bio, etc.)\n"

        if custom_instructions:
            prompt += f"\nADDITIONAL INSTRUCTIONS:\n{custom_instructions}\n"

        prompt += "\nWrite only the caption text, nothing else."

        return prompt

    async def _generate_hashtags(
        self,
        *,
        services_performed: List[str],
        techniques_used: List[str],
        tags: Optional[List[str]],
        count: int = 15
    ) -> List[str]:
        """Generate relevant hashtags"""

        # Base hashtags always included
        base_hashtags = [
            "hairtransformation",
            "hairgoals",
            "salonlife",
            "hairstylist",
            "hairinspo"
        ]

        # Service-specific hashtags
        service_hashtags = []
        for service in services_performed:
            service_lower = service.lower().replace(" ", "")
            service_hashtags.append(service_lower)

        # Technique-specific hashtags
        technique_hashtags = []
        for technique in techniques_used:
            technique_lower = technique.lower().replace(" ", "").replace("-", "")
            technique_hashtags.append(technique_lower)

        # Color-specific hashtags
        color_hashtags = []
        if any("blonde" in s.lower() for s in services_performed + (tags or [])):
            color_hashtags.extend(["blondehair", "blondebalayage", "blondespecialist"])
        if any("brunette" in s.lower() or "brown" in s.lower() for s in services_performed + (tags or [])):
            color_hashtags.extend(["brunettehair", "brownhair", "brunettebalayage"])
        if any("red" in s.lower() for s in services_performed + (tags or [])):
            color_hashtags.extend(["redhair", "redhead", "copperhair"])

        # Combine and deduplicate
        all_hashtags = base_hashtags + service_hashtags + technique_hashtags + color_hashtags

        if tags:
            all_hashtags.extend([t.lower().replace(" ", "").replace("#", "") for t in tags])

        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for h in all_hashtags:
            h_clean = h.strip().lower()
            if h_clean and h_clean not in seen:
                seen.add(h_clean)
                unique_hashtags.append(h_clean)

        return unique_hashtags[:count]

    def _combine_caption_hashtags(
        self,
        caption: str,
        hashtags: List[str]
    ) -> str:
        """Combine caption and hashtags into full post text"""
        if not hashtags:
            return caption

        hashtag_str = " ".join(f"#{h}" for h in hashtags)
        return f"{caption}\n\n.\n.\n.\n{hashtag_str}"

    async def suggest_post_time(
        self,
        *,
        platform: str = "instagram",
        timezone: str = "America/New_York"
    ) -> Dict[str, Any]:
        """Suggest optimal posting times based on general best practices"""

        # General best times for Instagram (can be enhanced with actual analytics)
        best_times = {
            "instagram": {
                "weekday_hours": [9, 11, 14, 19],  # 9am, 11am, 2pm, 7pm
                "weekend_hours": [10, 11, 14],  # 10am, 11am, 2pm
                "best_days": ["Tuesday", "Wednesday", "Thursday"]
            },
            "tiktok": {
                "weekday_hours": [7, 12, 15, 19, 21],  # More spread throughout day
                "weekend_hours": [9, 12, 19],
                "best_days": ["Tuesday", "Thursday", "Friday"]
            }
        }

        platform_times = best_times.get(platform, best_times["instagram"])

        return {
            "platform": platform,
            "best_hours": platform_times["weekday_hours"],
            "best_days": platform_times["best_days"],
            "timezone": timezone,
            "note": "Based on general industry best practices. Connect analytics for personalized recommendations."
        }


# Singleton instance
ai_caption_service = AICaptionService()
