"""
SalonSync Notification Service
Handles email and SMS notifications for appointments, reminders, and marketing.
"""

import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.app_settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationService:
    """Service for sending email and SMS notifications."""

    def __init__(self):
        self.smtp_configured = all([
            settings.SMTP_HOST,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD
        ])
        self.twilio_configured = all([
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
            settings.TWILIO_PHONE_NUMBER
        ])

        if self.twilio_configured:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
            except ImportError:
                logger.warning("Twilio package not installed. SMS notifications disabled.")
                self.twilio_configured = False
                self.twilio_client = None
        else:
            self.twilio_client = None

    # ==================== EMAIL METHODS ====================

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email notification."""
        if not self.smtp_configured:
            logger.warning(f"SMTP not configured. Would send email to {to_email}: {subject}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email

            # Plain text fallback
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))

            # HTML content
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    # ==================== SMS METHODS ====================

    def send_sms(self, to_phone: str, message: str) -> bool:
        """Send an SMS notification."""
        if not self.twilio_configured or not self.twilio_client:
            logger.warning(f"Twilio not configured. Would send SMS to {to_phone}: {message}")
            return False

        try:
            # Format phone number
            formatted_phone = self._format_phone(to_phone)

            self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=formatted_phone
            )
            logger.info(f"SMS sent to {to_phone}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {e}")
            return False

    def _format_phone(self, phone: str) -> str:
        """Format phone number for Twilio (E.164 format)."""
        # Remove any non-digit characters
        digits = "".join(filter(str.isdigit, phone))

        # Add country code if missing (assuming US)
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"+{digits}"

        return f"+{digits}"

    # ==================== APPOINTMENT NOTIFICATIONS ====================

    def send_appointment_confirmation(
        self,
        client_email: str,
        client_phone: Optional[str],
        client_name: str,
        salon_name: str,
        service_name: str,
        stylist_name: str,
        appointment_date: datetime,
        duration_minutes: int,
        salon_address: str,
        salon_phone: str,
        send_email: bool = True,
        send_sms: bool = True
    ) -> Dict[str, bool]:
        """Send appointment confirmation via email and/or SMS."""
        results = {"email": False, "sms": False}

        formatted_date = appointment_date.strftime("%A, %B %d, %Y")
        formatted_time = appointment_date.strftime("%I:%M %p")
        end_time = (appointment_date + timedelta(minutes=duration_minutes)).strftime("%I:%M %p")

        # Send Email
        if send_email and client_email:
            html_content = self._get_confirmation_email_html(
                client_name=client_name,
                salon_name=salon_name,
                service_name=service_name,
                stylist_name=stylist_name,
                date=formatted_date,
                time=formatted_time,
                end_time=end_time,
                salon_address=salon_address,
                salon_phone=salon_phone
            )
            text_content = f"""
Your appointment is confirmed!

{service_name} with {stylist_name}
{formatted_date} at {formatted_time}

{salon_name}
{salon_address}
{salon_phone}

See you soon!
            """.strip()

            results["email"] = self.send_email(
                to_email=client_email,
                subject=f"Appointment Confirmed - {salon_name}",
                html_content=html_content,
                text_content=text_content
            )

        # Send SMS
        if send_sms and client_phone:
            sms_message = (
                f"✅ Confirmed: {service_name} with {stylist_name} on "
                f"{formatted_date} at {formatted_time}. "
                f"See you at {salon_name}! Reply HELP for assistance."
            )
            results["sms"] = self.send_sms(client_phone, sms_message)

        return results

    def send_appointment_reminder(
        self,
        client_email: str,
        client_phone: Optional[str],
        client_name: str,
        salon_name: str,
        service_name: str,
        stylist_name: str,
        appointment_date: datetime,
        salon_address: str,
        salon_phone: str,
        hours_before: int = 24,
        send_email: bool = True,
        send_sms: bool = True
    ) -> Dict[str, bool]:
        """Send appointment reminder via email and/or SMS."""
        results = {"email": False, "sms": False}

        formatted_date = appointment_date.strftime("%A, %B %d")
        formatted_time = appointment_date.strftime("%I:%M %p")

        reminder_text = "tomorrow" if hours_before <= 24 else f"in {hours_before} hours"

        # Send Email
        if send_email and client_email:
            html_content = self._get_reminder_email_html(
                client_name=client_name,
                salon_name=salon_name,
                service_name=service_name,
                stylist_name=stylist_name,
                date=formatted_date,
                time=formatted_time,
                salon_address=salon_address,
                salon_phone=salon_phone,
                reminder_text=reminder_text
            )

            results["email"] = self.send_email(
                to_email=client_email,
                subject=f"Reminder: Your appointment is {reminder_text} - {salon_name}",
                html_content=html_content
            )

        # Send SMS
        if send_sms and client_phone:
            sms_message = (
                f"⏰ Reminder: {service_name} with {stylist_name} {reminder_text} "
                f"at {formatted_time}. {salon_name}. Reply C to confirm or R to reschedule."
            )
            results["sms"] = self.send_sms(client_phone, sms_message)

        return results

    def send_appointment_cancelled(
        self,
        client_email: str,
        client_phone: Optional[str],
        client_name: str,
        salon_name: str,
        service_name: str,
        appointment_date: datetime,
        cancelled_by: str = "salon",
        send_email: bool = True,
        send_sms: bool = True
    ) -> Dict[str, bool]:
        """Send appointment cancellation notification."""
        results = {"email": False, "sms": False}

        formatted_date = appointment_date.strftime("%A, %B %d at %I:%M %p")

        # Send Email
        if send_email and client_email:
            html_content = self._get_cancellation_email_html(
                client_name=client_name,
                salon_name=salon_name,
                service_name=service_name,
                date=formatted_date,
                cancelled_by=cancelled_by
            )

            results["email"] = self.send_email(
                to_email=client_email,
                subject=f"Appointment Cancelled - {salon_name}",
                html_content=html_content
            )

        # Send SMS
        if send_sms and client_phone:
            sms_message = (
                f"Your {service_name} appointment on {formatted_date} "
                f"has been cancelled. Book again at {salon_name}!"
            )
            results["sms"] = self.send_sms(client_phone, sms_message)

        return results

    def send_no_show_followup(
        self,
        client_email: str,
        client_name: str,
        salon_name: str,
        service_name: str,
        appointment_date: datetime
    ) -> bool:
        """Send follow-up email after a no-show."""
        formatted_date = appointment_date.strftime("%A, %B %d")

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7c3aed;">We missed you!</h2>
            <p>Hi {client_name},</p>
            <p>We noticed you weren't able to make your {service_name} appointment on {formatted_date}.</p>
            <p>Life happens! If you'd like to reschedule, we'd love to see you.</p>
            <p style="margin-top: 20px;">
                <a href="#" style="background: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">
                    Book Again
                </a>
            </p>
            <p style="color: #666; margin-top: 30px;">
                Best,<br>
                The {salon_name} Team
            </p>
        </div>
        """

        return self.send_email(
            to_email=client_email,
            subject=f"We missed you! - {salon_name}",
            html_content=html_content
        )

    # ==================== MARKETING NOTIFICATIONS ====================

    def send_birthday_message(
        self,
        client_email: str,
        client_name: str,
        salon_name: str,
        offer_text: Optional[str] = None
    ) -> bool:
        """Send birthday greeting with optional offer."""
        offer_section = ""
        if offer_text:
            offer_section = f"""
            <div style="background: #f3e8ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="font-size: 18px; color: #7c3aed; margin: 0;">🎁 Your Birthday Gift</p>
                <p style="margin: 10px 0 0 0;">{offer_text}</p>
            </div>
            """

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7c3aed;">🎂 Happy Birthday, {client_name}!</h2>
            <p>Wishing you an amazing day filled with joy!</p>
            {offer_section}
            <p>Treat yourself to some self-care this birthday season. We'd love to pamper you!</p>
            <p style="color: #666; margin-top: 30px;">
                With love,<br>
                The {salon_name} Team
            </p>
        </div>
        """

        return self.send_email(
            to_email=client_email,
            subject=f"🎂 Happy Birthday from {salon_name}!",
            html_content=html_content
        )

    def send_win_back_message(
        self,
        client_email: str,
        client_name: str,
        salon_name: str,
        days_since_visit: int,
        offer_text: Optional[str] = None
    ) -> bool:
        """Send re-engagement message to inactive clients."""
        offer_section = ""
        if offer_text:
            offer_section = f"""
            <div style="background: #f3e8ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="font-size: 18px; color: #7c3aed; margin: 0;">Special Offer Just For You</p>
                <p style="margin: 10px 0 0 0;">{offer_text}</p>
            </div>
            """

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7c3aed;">We miss you, {client_name}! 💜</h2>
            <p>It's been a while since your last visit, and we'd love to see you again.</p>
            {offer_section}
            <p>Ready to book? We can't wait to catch up!</p>
            <p style="margin-top: 20px;">
                <a href="#" style="background: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">
                    Book Now
                </a>
            </p>
            <p style="color: #666; margin-top: 30px;">
                See you soon,<br>
                The {salon_name} Team
            </p>
        </div>
        """

        return self.send_email(
            to_email=client_email,
            subject=f"We miss you! Come back to {salon_name}",
            html_content=html_content
        )

    def send_review_request(
        self,
        client_email: str,
        client_name: str,
        salon_name: str,
        service_name: str,
        stylist_name: str,
        review_url: Optional[str] = None
    ) -> bool:
        """Send post-visit review request."""
        review_link = review_url or "#"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #7c3aed;">How was your visit?</h2>
            <p>Hi {client_name},</p>
            <p>Thank you for visiting {salon_name}! We hope you loved your {service_name} with {stylist_name}.</p>
            <p>Your feedback helps us improve and helps others discover our salon. Would you mind leaving a quick review?</p>
            <p style="margin-top: 20px;">
                <a href="{review_link}" style="background: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">
                    Leave a Review ⭐
                </a>
            </p>
            <p style="color: #666; margin-top: 30px;">
                Thank you!<br>
                The {salon_name} Team
            </p>
        </div>
        """

        return self.send_email(
            to_email=client_email,
            subject=f"How was your visit to {salon_name}?",
            html_content=html_content
        )

    # ==================== EMAIL TEMPLATES ====================

    def _get_confirmation_email_html(
        self,
        client_name: str,
        salon_name: str,
        service_name: str,
        stylist_name: str,
        date: str,
        time: str,
        end_time: str,
        salon_address: str,
        salon_phone: str
    ) -> str:
        """Generate appointment confirmation email HTML."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%); padding: 40px 20px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">✓ Appointment Confirmed</h1>
                </div>

                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <p style="font-size: 16px; color: #333;">Hi {client_name},</p>
                    <p style="font-size: 16px; color: #333;">Your appointment has been confirmed. We look forward to seeing you!</p>

                    <!-- Appointment Card -->
                    <div style="background: #f8f5ff; border-radius: 12px; padding: 25px; margin: 25px 0; border-left: 4px solid #7c3aed;">
                        <h3 style="margin: 0 0 15px 0; color: #7c3aed;">{service_name}</h3>
                        <p style="margin: 8px 0; color: #666;">
                            <strong>Date:</strong> {date}
                        </p>
                        <p style="margin: 8px 0; color: #666;">
                            <strong>Time:</strong> {time} - {end_time}
                        </p>
                        <p style="margin: 8px 0; color: #666;">
                            <strong>With:</strong> {stylist_name}
                        </p>
                    </div>

                    <!-- Location -->
                    <div style="background: #f9f9f9; border-radius: 12px; padding: 20px; margin: 25px 0;">
                        <p style="margin: 0 0 8px 0; font-weight: bold; color: #333;">📍 {salon_name}</p>
                        <p style="margin: 0 0 8px 0; color: #666;">{salon_address}</p>
                        <p style="margin: 0; color: #666;">📞 {salon_phone}</p>
                    </div>

                    <!-- Buttons -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="#" style="display: inline-block; background: #7c3aed; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 5px;">
                            Add to Calendar
                        </a>
                        <a href="#" style="display: inline-block; background: white; color: #7c3aed; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; border: 2px solid #7c3aed; margin: 5px;">
                            Reschedule
                        </a>
                    </div>

                    <p style="font-size: 14px; color: #999; text-align: center;">
                        Need to cancel? Please let us know at least 24 hours in advance.
                    </p>
                </div>

                <!-- Footer -->
                <div style="background: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        Powered by SalonSync
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_reminder_email_html(
        self,
        client_name: str,
        salon_name: str,
        service_name: str,
        stylist_name: str,
        date: str,
        time: str,
        salon_address: str,
        salon_phone: str,
        reminder_text: str
    ) -> str:
        """Generate appointment reminder email HTML."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%); padding: 40px 20px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">⏰ Appointment Reminder</h1>
                </div>

                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <p style="font-size: 16px; color: #333;">Hi {client_name},</p>
                    <p style="font-size: 16px; color: #333;">Just a friendly reminder that your appointment is <strong>{reminder_text}</strong>!</p>

                    <!-- Appointment Card -->
                    <div style="background: #fef3c7; border-radius: 12px; padding: 25px; margin: 25px 0; border-left: 4px solid #f59e0b;">
                        <h3 style="margin: 0 0 15px 0; color: #92400e;">{service_name}</h3>
                        <p style="margin: 8px 0; color: #666;">
                            <strong>📅</strong> {date} at {time}
                        </p>
                        <p style="margin: 8px 0; color: #666;">
                            <strong>💇</strong> With {stylist_name}
                        </p>
                        <p style="margin: 8px 0; color: #666;">
                            <strong>📍</strong> {salon_name}
                        </p>
                    </div>

                    <!-- Buttons -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="#" style="display: inline-block; background: #22c55e; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 5px;">
                            ✓ Confirm Appointment
                        </a>
                    </div>

                    <p style="font-size: 14px; color: #666; text-align: center;">
                        Need to make changes? <a href="#" style="color: #7c3aed;">Reschedule</a> or <a href="#" style="color: #7c3aed;">Cancel</a>
                    </p>
                </div>

                <!-- Footer -->
                <div style="background: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 14px; margin: 0 0 10px 0;">
                        {salon_address}<br>
                        {salon_phone}
                    </p>
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        Powered by SalonSync
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_cancellation_email_html(
        self,
        client_name: str,
        salon_name: str,
        service_name: str,
        date: str,
        cancelled_by: str
    ) -> str:
        """Generate appointment cancellation email HTML."""
        message = "Your appointment has been cancelled as requested." if cancelled_by == "client" else "Unfortunately, we had to cancel your appointment."

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white;">
                <!-- Header -->
                <div style="background: #6b7280; padding: 40px 20px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">Appointment Cancelled</h1>
                </div>

                <!-- Content -->
                <div style="padding: 40px 30px;">
                    <p style="font-size: 16px; color: #333;">Hi {client_name},</p>
                    <p style="font-size: 16px; color: #333;">{message}</p>

                    <!-- Appointment Card -->
                    <div style="background: #f3f4f6; border-radius: 12px; padding: 25px; margin: 25px 0; opacity: 0.8;">
                        <p style="margin: 0; color: #666; text-decoration: line-through;">
                            {service_name} - {date}
                        </p>
                    </div>

                    <p style="font-size: 16px; color: #333;">We'd love to see you again! Book a new appointment whenever you're ready.</p>

                    <!-- Button -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="#" style="display: inline-block; background: #7c3aed; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                            Book New Appointment
                        </a>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 14px; margin: 0 0 10px 0;">
                        {salon_name}
                    </p>
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        Powered by SalonSync
                    </p>
                </div>
            </div>
        </body>
        </html>
        """


# Singleton instance
notification_service = NotificationService()
