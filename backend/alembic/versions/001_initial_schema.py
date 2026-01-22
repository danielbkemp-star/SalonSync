"""Initial SalonSync schema

Revision ID: 001
Revises:
Create Date: 2024-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === SALONS TABLE ===
    op.create_table(
        'salons',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('slug', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('cover_photo_url', sa.String(500), nullable=True),

        # Contact
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),

        # Location
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('zip_code', sa.String(20), nullable=True),
        sa.Column('country', sa.String(100), server_default='USA'),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('timezone', sa.String(50), server_default='America/New_York'),
        sa.Column('business_hours', sa.Text(), nullable=True),

        # Social Media
        sa.Column('instagram_handle', sa.String(100), nullable=True),
        sa.Column('instagram_access_token', sa.Text(), nullable=True),
        sa.Column('instagram_user_id', sa.String(100), nullable=True),
        sa.Column('instagram_token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('tiktok_handle', sa.String(100), nullable=True),
        sa.Column('tiktok_access_token', sa.Text(), nullable=True),
        sa.Column('tiktok_refresh_token', sa.Text(), nullable=True),
        sa.Column('tiktok_open_id', sa.String(100), nullable=True),
        sa.Column('tiktok_token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('facebook_page_id', sa.String(100), nullable=True),
        sa.Column('facebook_access_token', sa.Text(), nullable=True),

        # Payment Integration
        sa.Column('stripe_account_id', sa.String(255), nullable=True),
        sa.Column('stripe_onboarding_complete', sa.Boolean(), server_default='false'),
        sa.Column('stripe_charges_enabled', sa.Boolean(), server_default='false'),
        sa.Column('stripe_payouts_enabled', sa.Boolean(), server_default='false'),
        sa.Column('square_merchant_id', sa.String(255), nullable=True),
        sa.Column('square_access_token', sa.Text(), nullable=True),
        sa.Column('square_location_id', sa.String(255), nullable=True),

        # Subscription
        sa.Column('subscription_tier', sa.String(50), server_default='free'),
        sa.Column('subscription_status', sa.String(50), server_default='active'),
        sa.Column('subscription_started_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_ends_at', sa.DateTime(), nullable=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('features_enabled', sa.Text(), nullable=True),

        # Settings
        sa.Column('booking_lead_time_hours', sa.Integer(), server_default='2'),
        sa.Column('booking_window_days', sa.Integer(), server_default='60'),
        sa.Column('cancellation_policy_hours', sa.Integer(), server_default='24'),
        sa.Column('deposit_required', sa.Boolean(), server_default='false'),
        sa.Column('deposit_percentage', sa.Numeric(5, 2), server_default='0'),
        sa.Column('auto_confirm_appointments', sa.Boolean(), server_default='true'),
        sa.Column('send_confirmation_emails', sa.Boolean(), server_default='true'),
        sa.Column('send_reminder_emails', sa.Boolean(), server_default='true'),
        sa.Column('reminder_hours_before', sa.Integer(), server_default='24'),

        # Owner & Status
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # === USERS TABLE ===
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', index=True),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),
        sa.Column('is_superuser', sa.Boolean(), server_default='false'),

        # Profile
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),

        # Role
        sa.Column('role', sa.String(50), server_default='Client', index=True),
        sa.Column('permissions', postgresql.JSON(), server_default='[]'),

        # Session tracking
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('last_ip_address', sa.String(45), nullable=True),

        # Preferences
        sa.Column('preferences', postgresql.JSON(), server_default='{}'),
        sa.Column('notification_email', sa.Boolean(), server_default='true'),
        sa.Column('notification_sms', sa.Boolean(), server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),

        # Security
        sa.Column('password_reset_token', sa.String(500), unique=True, nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('must_change_password', sa.Boolean(), server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # === STAFF TABLE ===
    op.create_table(
        'staff',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('salon_id', sa.Integer(), sa.ForeignKey('salons.id'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), unique=True, nullable=False),

        # Professional info
        sa.Column('title', sa.String(100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('profile_photo_url', sa.String(500), nullable=True),
        sa.Column('specialties', postgresql.JSON(), server_default='[]'),
        sa.Column('certifications', postgresql.JSON(), server_default='[]'),
        sa.Column('years_experience', sa.Integer(), nullable=True),

        # Social
        sa.Column('instagram_handle', sa.String(100), nullable=True),
        sa.Column('tiktok_handle', sa.String(100), nullable=True),
        sa.Column('portfolio_url', sa.String(500), nullable=True),

        # Employment
        sa.Column('status', sa.String(50), server_default='active', index=True),
        sa.Column('hire_date', sa.DateTime(), nullable=True),
        sa.Column('termination_date', sa.DateTime(), nullable=True),
        sa.Column('commission_rate', sa.Numeric(5, 2), server_default='0'),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('salary', sa.Numeric(12, 2), nullable=True),

        # Schedule
        sa.Column('default_schedule', postgresql.JSON(), server_default='{}'),
        sa.Column('accepts_walkins', sa.Boolean(), server_default='true'),
        sa.Column('booking_buffer_mins', sa.Integer(), server_default='0'),
        sa.Column('service_ids', postgresql.JSON(), server_default='[]'),

        # Display
        sa.Column('display_order', sa.Integer(), server_default='0'),
        sa.Column('show_on_booking', sa.Boolean(), server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # === CLIENTS TABLE ===
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('salon_id', sa.Integer(), sa.ForeignKey('salons.id'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), unique=True, nullable=True),

        # Contact
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), nullable=True, index=True),
        sa.Column('phone', sa.String(50), nullable=True, index=True),
        sa.Column('phone_secondary', sa.String(50), nullable=True),

        # Address
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('zip_code', sa.String(20), nullable=True),

        # Social
        sa.Column('instagram_handle', sa.String(100), nullable=True),
        sa.Column('tiktok_handle', sa.String(100), nullable=True),

        # Preferences
        sa.Column('preferred_staff_id', sa.Integer(), sa.ForeignKey('staff.id'), nullable=True),
        sa.Column('preferred_services', postgresql.JSON(), server_default='[]'),
        sa.Column('communication_preference', sa.String(20), server_default='email'),
        sa.Column('marketing_opt_in', sa.Boolean(), server_default='false'),

        # Hair/Beauty profile
        sa.Column('hair_type', sa.String(50), nullable=True),
        sa.Column('hair_color', sa.String(50), nullable=True),
        sa.Column('current_hair_color', sa.String(100), nullable=True),
        sa.Column('hair_texture', sa.String(50), nullable=True),
        sa.Column('hair_length', sa.String(50), nullable=True),
        sa.Column('hair_density', sa.String(50), nullable=True),
        sa.Column('hair_porosity', sa.String(50), nullable=True),
        sa.Column('hair_color_history', postgresql.JSON(), server_default='[]'),
        sa.Column('skin_type', sa.String(50), nullable=True),
        sa.Column('skin_tone', sa.String(50), nullable=True),
        sa.Column('allergies', sa.Text(), nullable=True),
        sa.Column('scalp_conditions', sa.Text(), nullable=True),
        sa.Column('special_notes', sa.Text(), nullable=True),

        # Consent
        sa.Column('photo_consent', sa.Boolean(), server_default='false'),
        sa.Column('social_media_consent', sa.Boolean(), server_default='false'),
        sa.Column('website_consent', sa.Boolean(), server_default='false'),
        sa.Column('sms_consent', sa.Boolean(), server_default='false'),
        sa.Column('consent_updated_at', sa.DateTime(), nullable=True),

        # Loyalty
        sa.Column('loyalty_points', sa.Integer(), server_default='0'),
        sa.Column('loyalty_tier', sa.String(50), server_default='bronze'),
        sa.Column('referral_code', sa.String(20), unique=True, nullable=True),
        sa.Column('referred_by_id', sa.Integer(), sa.ForeignKey('clients.id'), nullable=True),

        # Financials
        sa.Column('total_spent', sa.Numeric(12, 2), server_default='0'),
        sa.Column('average_ticket', sa.Numeric(10, 2), server_default='0'),
        sa.Column('outstanding_balance', sa.Numeric(10, 2), server_default='0'),

        # Stats
        sa.Column('visit_count', sa.Integer(), server_default='0'),
        sa.Column('last_visit', sa.DateTime(), nullable=True),
        sa.Column('next_appointment', sa.DateTime(), nullable=True),
        sa.Column('cancellation_count', sa.Integer(), server_default='0'),
        sa.Column('no_show_count', sa.Integer(), server_default='0'),

        # Dates
        sa.Column('birthday', sa.DateTime(), nullable=True),
        sa.Column('anniversary', sa.DateTime(), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_vip', sa.Boolean(), server_default='false'),
        sa.Column('is_blocked', sa.Boolean(), server_default='false'),
        sa.Column('blocked_reason', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSON(), server_default='[]'),
        sa.Column('source', sa.String(50), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # === SERVICES TABLE ===
    op.create_table(
        'services',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('salon_id', sa.Integer(), sa.ForeignKey('salons.id'), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=False, index=True),

        # Pricing
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('price_min', sa.Numeric(10, 2), nullable=True),
        sa.Column('price_max', sa.Numeric(10, 2), nullable=True),
        sa.Column('is_price_variable', sa.Boolean(), server_default='false'),

        # Duration
        sa.Column('duration_mins', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('buffer_before_mins', sa.Integer(), server_default='0'),
        sa.Column('buffer_after_mins', sa.Integer(), server_default='0'),
        sa.Column('processing_time_mins', sa.Integer(), server_default='0'),

        # Availability
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_online_bookable', sa.Boolean(), server_default='true'),
        sa.Column('requires_consultation', sa.Boolean(), server_default='false'),
        sa.Column('is_addon', sa.Boolean(), server_default='false'),

        # Staff
        sa.Column('required_staff_count', sa.Integer(), server_default='1'),
        sa.Column('skill_level_required', sa.String(50), nullable=True),

        # Commission
        sa.Column('commission_type', sa.String(20), server_default='percentage'),
        sa.Column('commission_value', sa.Numeric(10, 2), nullable=True),

        # Display
        sa.Column('display_order', sa.Integer(), server_default='0'),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('tags', postgresql.JSON(), server_default='[]'),
        sa.Column('search_keywords', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # === APPOINTMENTS TABLE ===
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('salon_id', sa.Integer(), sa.ForeignKey('salons.id'), nullable=False, index=True),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id'), nullable=False, index=True),
        sa.Column('staff_id', sa.Integer(), sa.ForeignKey('staff.id'), nullable=False, index=True),

        # Timing
        sa.Column('start_time', sa.DateTime(), nullable=False, index=True),
        sa.Column('end_time', sa.DateTime(), nullable=False, index=True),
        sa.Column('duration_mins', sa.Integer(), nullable=False),

        # Status
        sa.Column('status', sa.String(50), server_default='scheduled', index=True),
        sa.Column('source', sa.String(50), server_default='online'),

        # Check-in
        sa.Column('checked_in_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),

        # Pricing
        sa.Column('estimated_total', sa.Numeric(10, 2), nullable=True),
        sa.Column('final_total', sa.Numeric(10, 2), nullable=True),
        sa.Column('deposit_amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('deposit_paid', sa.Boolean(), server_default='false'),

        # Notes
        sa.Column('client_notes', sa.Text(), nullable=True),
        sa.Column('staff_notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),

        # Confirmation/Reminder
        sa.Column('confirmation_sent', sa.Boolean(), server_default='false'),
        sa.Column('confirmation_sent_at', sa.DateTime(), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), server_default='false'),
        sa.Column('reminder_sent_at', sa.DateTime(), nullable=True),

        # Cancellation
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.String(50), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('cancellation_fee', sa.Numeric(10, 2), server_default='0'),

        # Recurring
        sa.Column('is_recurring', sa.Boolean(), server_default='false'),
        sa.Column('recurring_pattern', postgresql.JSON(), nullable=True),
        sa.Column('parent_appointment_id', sa.Integer(), sa.ForeignKey('appointments.id'), nullable=True),

        # Display
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('payment_status', sa.String(50), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )

    # === APPOINTMENT_SERVICES TABLE ===
    op.create_table(
        'appointment_services',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('appointment_id', sa.Integer(), sa.ForeignKey('appointments.id'), nullable=False),
        sa.Column('service_id', sa.Integer(), sa.ForeignKey('services.id'), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('duration_mins', sa.Integer(), nullable=False),
        sa.Column('sequence', sa.Integer(), server_default='0'),
    )

    # === MEDIA_SETS TABLE (Formula Vault) ===
    op.create_table(
        'media_sets',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('salon_id', sa.Integer(), sa.ForeignKey('salons.id'), nullable=False, index=True),
        sa.Column('staff_id', sa.Integer(), sa.ForeignKey('staff.id'), nullable=False, index=True),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id'), nullable=True, index=True),
        sa.Column('appointment_id', sa.Integer(), sa.ForeignKey('appointments.id'), unique=True, nullable=True),

        # Title
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        # Photos
        sa.Column('before_photo_url', sa.String(500), nullable=True),
        sa.Column('before_photo_public_id', sa.String(255), nullable=True),
        sa.Column('before_photo_taken_at', sa.DateTime(), nullable=True),
        sa.Column('after_photo_url', sa.String(500), nullable=True),
        sa.Column('after_photo_public_id', sa.String(255), nullable=True),
        sa.Column('after_photo_taken_at', sa.DateTime(), nullable=True),
        sa.Column('comparison_photo_url', sa.String(500), nullable=True),
        sa.Column('comparison_photo_public_id', sa.String(255), nullable=True),
        sa.Column('additional_photos', postgresql.JSON(), server_default='[]'),

        # Services & Formulas
        sa.Column('services_performed', postgresql.JSON(), server_default='[]'),
        sa.Column('color_formulas', postgresql.JSON(), server_default='[]'),
        sa.Column('products_used', postgresql.JSON(), server_default='[]'),
        sa.Column('techniques_used', postgresql.JSON(), server_default='[]'),

        # Processing
        sa.Column('total_processing_time', sa.String(100), nullable=True),
        sa.Column('total_service_time', sa.String(100), nullable=True),

        # Hair details
        sa.Column('starting_level', sa.String(50), nullable=True),
        sa.Column('target_level', sa.String(50), nullable=True),
        sa.Column('achieved_level', sa.String(50), nullable=True),
        sa.Column('hair_condition_before', sa.String(100), nullable=True),
        sa.Column('hair_condition_after', sa.String(100), nullable=True),
        sa.Column('porosity', sa.String(50), nullable=True),

        # Social
        sa.Column('tags', postgresql.JSON(), server_default='[]'),
        sa.Column('ai_generated_caption', sa.Text(), nullable=True),
        sa.Column('ai_generation_prompt', sa.Text(), nullable=True),
        sa.Column('suggested_hashtags', postgresql.JSON(), server_default='[]'),

        # Consent
        sa.Column('client_photo_consent', sa.Boolean(), server_default='false'),
        sa.Column('client_social_consent', sa.Boolean(), server_default='false'),
        sa.Column('client_website_consent', sa.Boolean(), server_default='false'),
        sa.Column('consent_recorded_at', sa.DateTime(), nullable=True),
        sa.Column('consent_method', sa.String(50), nullable=True),

        # Portfolio
        sa.Column('is_portfolio_piece', sa.Boolean(), server_default='false'),
        sa.Column('is_featured', sa.Boolean(), server_default='false'),
        sa.Column('is_private', sa.Boolean(), server_default='false'),
        sa.Column('photo_quality_rating', sa.Integer(), nullable=True),

        # Notes
        sa.Column('stylist_notes', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('maintenance_tips', sa.Text(), nullable=True),
        sa.Column('client_satisfaction', sa.Integer(), nullable=True),
        sa.Column('client_feedback', sa.Text(), nullable=True),

        # Dates
        sa.Column('service_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # === SOCIAL_POSTS TABLE ===
    op.create_table(
        'social_posts',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('salon_id', sa.Integer(), sa.ForeignKey('salons.id'), nullable=False, index=True),
        sa.Column('media_set_id', sa.Integer(), sa.ForeignKey('media_sets.id'), nullable=True, index=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),

        # Platform
        sa.Column('platform', sa.String(50), nullable=False, index=True),

        # Content
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('hashtags', postgresql.JSON(), server_default='[]'),
        sa.Column('media_urls', postgresql.JSON(), server_default='[]'),
        sa.Column('is_carousel', sa.Boolean(), server_default='false'),
        sa.Column('carousel_order', postgresql.JSON(), server_default='[]'),
        sa.Column('video_url', sa.String(500), nullable=True),
        sa.Column('video_thumbnail_url', sa.String(500), nullable=True),
        sa.Column('video_duration_seconds', sa.Integer(), nullable=True),

        # AI
        sa.Column('caption_generated_by_ai', sa.Boolean(), server_default='false'),
        sa.Column('ai_generation_prompt', sa.Text(), nullable=True),
        sa.Column('ai_model_used', sa.String(100), nullable=True),
        sa.Column('ai_generation_timestamp', sa.DateTime(), nullable=True),
        sa.Column('original_ai_caption', sa.Text(), nullable=True),
        sa.Column('caption_edited', sa.Boolean(), server_default='false'),

        # Status & Scheduling
        sa.Column('status', sa.String(50), server_default='draft', index=True),
        sa.Column('scheduled_time', sa.DateTime(), nullable=True, index=True),
        sa.Column('published_time', sa.DateTime(), nullable=True),
        sa.Column('publish_attempts', sa.Integer(), server_default='0'),
        sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(100), nullable=True),

        # Platform response
        sa.Column('platform_post_id', sa.String(255), nullable=True, index=True),
        sa.Column('platform_post_url', sa.String(500), nullable=True),
        sa.Column('platform_media_id', sa.String(255), nullable=True),
        sa.Column('platform_response', postgresql.JSON(), nullable=True),

        # Engagement
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('comments', sa.Integer(), nullable=True),
        sa.Column('shares', sa.Integer(), nullable=True),
        sa.Column('saves', sa.Integer(), nullable=True),
        sa.Column('reach', sa.Integer(), nullable=True),
        sa.Column('impressions', sa.Integer(), nullable=True),
        sa.Column('video_views', sa.Integer(), nullable=True),
        sa.Column('video_watch_time_seconds', sa.Integer(), nullable=True),
        sa.Column('avg_watch_percentage', sa.Integer(), nullable=True),
        sa.Column('replies', sa.Integer(), nullable=True),
        sa.Column('exits', sa.Integer(), nullable=True),
        sa.Column('taps_forward', sa.Integer(), nullable=True),
        sa.Column('taps_back', sa.Integer(), nullable=True),
        sa.Column('engagement_rate', sa.String(10), nullable=True),
        sa.Column('engagement_updated_at', sa.DateTime(), nullable=True),
        sa.Column('metrics_history', postgresql.JSON(), server_default='[]'),

        # Tagging
        sa.Column('client_tagged', sa.Boolean(), server_default='false'),
        sa.Column('client_instagram_handle', sa.String(100), nullable=True),
        sa.Column('location_id', sa.String(255), nullable=True),
        sa.Column('location_name', sa.String(255), nullable=True),
        sa.Column('product_tags', postgresql.JSON(), server_default='[]'),

        # Approval
        sa.Column('requires_approval', sa.Boolean(), server_default='false'),
        sa.Column('approved', sa.Boolean(), server_default='false'),
        sa.Column('approved_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),

        # Notes
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('suggested_post_time', sa.DateTime(), nullable=True),
        sa.Column('suggestion_reason', sa.String(255), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create additional indexes
    op.create_index('ix_appointments_date_salon', 'appointments', ['salon_id', 'start_time'])
    op.create_index('ix_clients_salon_name', 'clients', ['salon_id', 'last_name', 'first_name'])
    op.create_index('ix_media_sets_salon_date', 'media_sets', ['salon_id', 'service_date'])


def downgrade() -> None:
    op.drop_table('social_posts')
    op.drop_table('media_sets')
    op.drop_table('appointment_services')
    op.drop_table('appointments')
    op.drop_table('services')
    op.drop_table('clients')
    op.drop_table('staff')
    op.drop_table('users')
    op.drop_table('salons')
