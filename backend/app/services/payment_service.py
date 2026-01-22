"""
Payment Service - Stripe Connect integration for salon payments
Handles connected accounts, payment intents, and payouts
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

import stripe

from app.app_settings import settings
from app.models import Salon, Appointment, Sale

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Stripe Connect payment service for multi-tenant salon payments.

    Uses Stripe Connect Express for salon onboarding with platform fees.
    """

    def __init__(self):
        self._configured = False
        self._configure()

    def _configure(self):
        """Configure Stripe API"""
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            self._configured = True
        else:
            logger.warning("Stripe API key not configured - payments disabled")

    @property
    def is_configured(self) -> bool:
        return self._configured

    # =========================================================================
    # Stripe Connect Account Management
    # =========================================================================

    async def create_connect_account(
        self,
        salon: Salon,
        *,
        owner_email: str,
        business_type: str = "company",
        country: str = "US"
    ) -> str:
        """
        Create a Stripe Connect Express account for a salon.

        Args:
            salon: Salon model instance
            owner_email: Email of the salon owner
            business_type: "individual" or "company"
            country: Two-letter country code

        Returns:
            Stripe account ID
        """
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        try:
            account = stripe.Account.create(
                type="express",
                country=country,
                email=owner_email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                business_type=business_type,
                business_profile={
                    "name": salon.name,
                    "mcc": "7230",  # Beauty Shops / Barber and Beauty Shops
                    "url": salon.website if hasattr(salon, 'website') and salon.website else None,
                },
                metadata={
                    "salon_id": str(salon.id),
                    "salon_name": salon.name,
                    "platform": "salonsync"
                }
            )

            logger.info(f"Created Stripe Connect account {account.id} for salon {salon.id}")
            return account.id

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Connect account: {e}")
            raise

    async def create_onboarding_link(
        self,
        account_id: str,
        return_url: str,
        refresh_url: str
    ) -> str:
        """
        Generate Stripe onboarding URL for a connected account.

        Args:
            account_id: Stripe account ID
            return_url: URL to redirect to after onboarding
            refresh_url: URL to redirect to if link expires

        Returns:
            Onboarding URL
        """
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        try:
            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type="account_onboarding"
            )

            return account_link.url

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create onboarding link: {e}")
            raise

    async def create_login_link(self, account_id: str) -> str:
        """
        Generate a Stripe Express dashboard login link.

        Args:
            account_id: Stripe account ID

        Returns:
            Dashboard login URL
        """
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        try:
            login_link = stripe.Account.create_login_link(account_id)
            return login_link.url

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create login link: {e}")
            raise

    async def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        Get the status of a connected account.

        Returns:
            Dict with charges_enabled, payouts_enabled, requirements, etc.
        """
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        try:
            account = stripe.Account.retrieve(account_id)

            return {
                "account_id": account.id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted,
                "requirements": {
                    "currently_due": account.requirements.currently_due if account.requirements else [],
                    "eventually_due": account.requirements.eventually_due if account.requirements else [],
                    "past_due": account.requirements.past_due if account.requirements else [],
                    "disabled_reason": account.requirements.disabled_reason if account.requirements else None
                },
                "capabilities": {
                    "card_payments": account.capabilities.card_payments if account.capabilities else None,
                    "transfers": account.capabilities.transfers if account.capabilities else None
                },
                "business_profile": {
                    "name": account.business_profile.name if account.business_profile else None,
                    "mcc": account.business_profile.mcc if account.business_profile else None
                }
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to get account status: {e}")
            raise

    # =========================================================================
    # Payment Processing
    # =========================================================================

    async def create_payment_intent(
        self,
        appointment: Appointment,
        *,
        amount: float,
        currency: str = "usd",
        application_fee_percent: float = 2.9,
        description: Optional[str] = None,
        customer_email: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent for an appointment.
        Uses Stripe Connect to route payment to salon's connected account.

        Args:
            appointment: Appointment model instance
            amount: Amount in dollars
            currency: Currency code
            application_fee_percent: Platform fee percentage (default 2.9%)
            description: Payment description
            customer_email: Customer email for receipt
            metadata: Additional metadata

        Returns:
            Dict with client_secret, payment_intent_id, etc.
        """
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        # Get salon's connected account
        salon = appointment.salon
        if not salon.stripe_account_id:
            raise ValueError("Salon has not connected Stripe account")

        # Calculate amounts in cents
        amount_cents = int(amount * 100)
        application_fee_cents = int(amount_cents * (application_fee_percent / 100))

        try:
            # Build metadata
            payment_metadata = {
                "salon_id": str(salon.id),
                "appointment_id": str(appointment.id),
                "platform": "salonsync"
            }
            if metadata:
                payment_metadata.update(metadata)

            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                application_fee_amount=application_fee_cents,
                transfer_data={
                    "destination": salon.stripe_account_id
                },
                description=description or f"Appointment #{appointment.id} at {salon.name}",
                receipt_email=customer_email,
                metadata=payment_metadata,
                automatic_payment_methods={"enabled": True}
            )

            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "amount": amount,
                "amount_cents": amount_cents,
                "application_fee": amount_cents * (application_fee_percent / 100) / 100,
                "currency": currency,
                "status": intent.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise

    async def create_checkout_session(
        self,
        *,
        salon: Salon,
        amount: float,
        description: str,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
        appointment_id: Optional[int] = None,
        application_fee_percent: float = 2.9,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session.
        Redirects customer to Stripe-hosted payment page.

        Returns:
            Dict with checkout_url and session_id
        """
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        amount_cents = int(amount * 100)
        application_fee_cents = int(amount_cents * (application_fee_percent / 100))

        try:
            session_metadata = {
                "salon_id": str(salon.id),
                "platform": "salonsync"
            }
            if appointment_id:
                session_metadata["appointment_id"] = str(appointment_id)
            if metadata:
                session_metadata.update(metadata)

            session_params = {
                "payment_method_types": ["card"],
                "line_items": [{
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": description,
                        },
                    },
                    "quantity": 1,
                }],
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": session_metadata
            }

            if customer_email:
                session_params["customer_email"] = customer_email

            # Use Connect if salon has account
            if salon.stripe_account_id:
                session_params["payment_intent_data"] = {
                    "application_fee_amount": application_fee_cents,
                    "transfer_data": {
                        "destination": salon.stripe_account_id
                    }
                }

            session = stripe.checkout.Session.create(**session_params)

            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "amount": amount,
                "expires_at": datetime.fromtimestamp(session.expires_at).isoformat()
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise

    async def get_checkout_session(self, session_id: str) -> Dict[str, Any]:
        """Get details of a checkout session."""
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        try:
            session = stripe.checkout.Session.retrieve(session_id)

            return {
                "session_id": session.id,
                "status": session.status,
                "payment_status": session.payment_status,
                "amount_total": session.amount_total / 100 if session.amount_total else 0,
                "customer_email": session.customer_email,
                "payment_intent": session.payment_intent,
                "metadata": dict(session.metadata) if session.metadata else {}
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve session: {e}")
            raise

    # =========================================================================
    # Refunds
    # =========================================================================

    async def create_refund(
        self,
        payment_intent_id: str,
        *,
        amount: Optional[float] = None,
        reason: Optional[str] = None,
        reverse_transfer: bool = True,
        refund_application_fee: bool = True
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment.

        Args:
            payment_intent_id: Original payment intent ID
            amount: Refund amount (None for full refund)
            reason: Reason for refund
            reverse_transfer: Whether to reverse the transfer to connected account
            refund_application_fee: Whether to refund the application fee

        Returns:
            Refund details
        """
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        try:
            refund_params = {
                "payment_intent": payment_intent_id,
                "reverse_transfer": reverse_transfer,
                "refund_application_fee": refund_application_fee
            }

            if amount:
                refund_params["amount"] = int(amount * 100)

            if reason:
                # Stripe accepts: duplicate, fraudulent, requested_by_customer
                refund_params["reason"] = reason

            refund = stripe.Refund.create(**refund_params)

            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100,
                "currency": refund.currency,
                "payment_intent": refund.payment_intent,
                "created": datetime.fromtimestamp(refund.created).isoformat()
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create refund: {e}")
            raise

    # =========================================================================
    # Webhooks
    # =========================================================================

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """
        Process and verify a Stripe webhook event.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header value

        Returns:
            Processed event data
        """
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        if not webhook_secret:
            raise RuntimeError("Stripe webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise ValueError("Invalid signature")

        # Process event based on type
        event_data = {
            "event_id": event.id,
            "event_type": event.type,
            "created": datetime.fromtimestamp(event.created).isoformat(),
            "data": {}
        }

        # Handle specific event types
        if event.type == "checkout.session.completed":
            session = event.data.object
            event_data["data"] = {
                "session_id": session.id,
                "payment_status": session.payment_status,
                "amount_total": session.amount_total / 100 if session.amount_total else 0,
                "metadata": dict(session.metadata) if session.metadata else {}
            }

        elif event.type == "payment_intent.succeeded":
            intent = event.data.object
            event_data["data"] = {
                "payment_intent_id": intent.id,
                "amount": intent.amount / 100,
                "metadata": dict(intent.metadata) if intent.metadata else {}
            }

        elif event.type == "payment_intent.payment_failed":
            intent = event.data.object
            event_data["data"] = {
                "payment_intent_id": intent.id,
                "error": intent.last_payment_error.message if intent.last_payment_error else "Unknown error",
                "metadata": dict(intent.metadata) if intent.metadata else {}
            }

        elif event.type == "charge.refunded":
            charge = event.data.object
            event_data["data"] = {
                "charge_id": charge.id,
                "amount_refunded": charge.amount_refunded / 100,
                "refunded": charge.refunded
            }

        elif event.type == "account.updated":
            account = event.data.object
            event_data["data"] = {
                "account_id": account.id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted
            }

        elif event.type == "payout.paid":
            payout = event.data.object
            event_data["data"] = {
                "payout_id": payout.id,
                "amount": payout.amount / 100,
                "arrival_date": datetime.fromtimestamp(payout.arrival_date).isoformat()
            }

        logger.info(f"Processed webhook event: {event.type}")
        return event_data

    # =========================================================================
    # Balance & Payouts
    # =========================================================================

    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """Get the balance of a connected account."""
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        try:
            balance = stripe.Balance.retrieve(stripe_account=account_id)

            available = {}
            pending = {}

            for item in balance.available:
                available[item.currency] = item.amount / 100

            for item in balance.pending:
                pending[item.currency] = item.amount / 100

            return {
                "account_id": account_id,
                "available": available,
                "pending": pending
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to get account balance: {e}")
            raise

    async def get_recent_payouts(
        self,
        account_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent payouts for a connected account."""
        if not self._configured:
            raise RuntimeError("Stripe not configured")

        try:
            payouts = stripe.Payout.list(
                limit=limit,
                stripe_account=account_id
            )

            return [{
                "payout_id": p.id,
                "amount": p.amount / 100,
                "currency": p.currency,
                "status": p.status,
                "arrival_date": datetime.fromtimestamp(p.arrival_date).isoformat(),
                "created": datetime.fromtimestamp(p.created).isoformat()
            } for p in payouts.data]

        except stripe.error.StripeError as e:
            logger.error(f"Failed to get payouts: {e}")
            raise


# Singleton instance
payment_service = PaymentService()
