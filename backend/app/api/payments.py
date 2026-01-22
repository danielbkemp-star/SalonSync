"""
Payments API Routes for SalonSync
Stripe integration for payment processing
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Salon, Sale, Appointment
from app.app_settings import get_settings
from app.schemas.base import MessageResponse
from app.api.dependencies import (
    CurrentUser, require_salon_access, SalonAccess
)

router = APIRouter()
settings = get_settings()


# ============================================================================
# Schemas
# ============================================================================

class CheckoutRequest(BaseModel):
    """Request to create a checkout session."""
    salon_id: int
    appointment_id: Optional[int] = None
    amount: float  # Amount in dollars
    description: str
    customer_email: Optional[str] = None
    success_url: str
    cancel_url: str
    metadata: Optional[dict] = None


class CheckoutResponse(BaseModel):
    """Checkout session response."""
    checkout_url: str
    session_id: str


class RefundRequest(BaseModel):
    """Request to process a refund."""
    payment_intent_id: str
    amount: Optional[float] = None  # If None, full refund
    reason: Optional[str] = None


class StripeConnectRequest(BaseModel):
    """Request to initiate Stripe Connect onboarding."""
    salon_id: int
    return_url: str
    refresh_url: str


# ============================================================================
# Checkout
# ============================================================================

@router.post("/payments/create-checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Checkout session.

    Returns a URL to redirect the customer to Stripe's hosted checkout page.
    """
    salon = await require_salon_access(request.salon_id, current_user, db)

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured"
        )

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Build metadata
        metadata = request.metadata or {}
        metadata["salon_id"] = str(request.salon_id)
        if request.appointment_id:
            metadata["appointment_id"] = str(request.appointment_id)

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(request.amount * 100),  # Stripe uses cents
                        "product_data": {
                            "name": request.description,
                        },
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            customer_email=request.customer_email,
            metadata=metadata,
            # Use connected account if salon has Stripe Connect
            stripe_account=salon.stripe_account_id if salon.stripe_account_id else None,
        )

        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.get("/payments/session/{session_id}")
async def get_checkout_session(
    session_id: str,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get status of a checkout session."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured"
        )

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        session = stripe.checkout.Session.retrieve(session_id)

        return {
            "id": session.id,
            "status": session.status,
            "payment_status": session.payment_status,
            "amount_total": session.amount_total / 100 if session.amount_total else 0,
            "customer_email": session.customer_email,
            "metadata": session.metadata,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )


# ============================================================================
# Webhooks
# ============================================================================

@router.post("/payments/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhooks.

    Processes payment events like successful payments, refunds, etc.
    """
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhooks not configured"
        )

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        payload = await request.body()

        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )

        # Handle specific events
        if event.type == "checkout.session.completed":
            session = event.data.object
            await _handle_checkout_completed(session, db)

        elif event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            await _handle_payment_succeeded(payment_intent, db)

        elif event.type == "payment_intent.payment_failed":
            payment_intent = event.data.object
            await _handle_payment_failed(payment_intent, db)

        elif event.type == "charge.refunded":
            charge = event.data.object
            await _handle_refund(charge, db)

        return {"status": "received"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook error: {str(e)}"
        )


async def _handle_checkout_completed(session, db: Session):
    """Handle successful checkout completion."""
    metadata = session.get("metadata", {})
    salon_id = metadata.get("salon_id")
    appointment_id = metadata.get("appointment_id")

    if appointment_id:
        appointment = db.query(Appointment).filter(
            Appointment.id == int(appointment_id)
        ).first()
        if appointment:
            appointment.deposit_paid = True
            appointment.deposit_amount = session.amount_total / 100
            db.commit()


async def _handle_payment_succeeded(payment_intent, db: Session):
    """Handle successful payment."""
    # Could update sale records, send receipts, etc.
    pass


async def _handle_payment_failed(payment_intent, db: Session):
    """Handle failed payment."""
    # Could notify staff, update appointment status, etc.
    pass


async def _handle_refund(charge, db: Session):
    """Handle refund processed."""
    # Could update sale records
    pass


# ============================================================================
# Stripe Connect (for salon payouts)
# ============================================================================

@router.post("/payments/connect/onboard")
async def initiate_connect_onboarding(
    request: StripeConnectRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Initiate Stripe Connect onboarding for a salon.

    Returns a URL to redirect the salon owner to complete onboarding.
    """
    salon = await SalonAccess(require_owner=True)(request.salon_id, current_user, db)

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured"
        )

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Create or retrieve connected account
        if salon.stripe_account_id:
            account = stripe.Account.retrieve(salon.stripe_account_id)
        else:
            account = stripe.Account.create(
                type="express",
                country="US",
                email=salon.email or current_user.email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                business_type="company",
                business_profile={
                    "name": salon.name,
                    "mcc": "7230",  # Beauty Shops
                },
                metadata={
                    "salon_id": str(salon.id),
                },
            )

            # Save account ID
            salon.stripe_account_id = account.id
            db.commit()

        # Create account link for onboarding
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=request.refresh_url,
            return_url=request.return_url,
            type="account_onboarding",
        )

        return {
            "onboarding_url": account_link.url,
            "account_id": account.id,
            "expires_at": account_link.expires_at,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate onboarding: {str(e)}"
        )


@router.get("/salons/{salon_id}/payment-status")
async def get_salon_payment_status(
    salon_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """Get the payment/Stripe Connect status for a salon."""
    salon = await require_salon_access(salon_id, current_user, db)

    if not salon.stripe_account_id:
        return {
            "stripe_connected": False,
            "charges_enabled": False,
            "payouts_enabled": False,
            "details_submitted": False,
            "onboarding_complete": False,
        }

    if not settings.STRIPE_SECRET_KEY:
        return {
            "stripe_connected": bool(salon.stripe_account_id),
            "charges_enabled": False,
            "payouts_enabled": False,
            "details_submitted": False,
            "onboarding_complete": False,
            "error": "Stripe not configured"
        }

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        account = stripe.Account.retrieve(salon.stripe_account_id)

        return {
            "stripe_connected": True,
            "account_id": account.id,
            "charges_enabled": account.charges_enabled,
            "payouts_enabled": account.payouts_enabled,
            "details_submitted": account.details_submitted,
            "onboarding_complete": account.charges_enabled and account.payouts_enabled,
            "requirements": account.requirements.currently_due if account.requirements else [],
        }

    except Exception as e:
        return {
            "stripe_connected": bool(salon.stripe_account_id),
            "error": str(e)
        }


@router.post("/payments/refund")
async def process_refund(
    request: RefundRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Process a refund for a payment.

    Requires manager role.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured"
        )

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        refund_params = {
            "payment_intent": request.payment_intent_id,
        }

        if request.amount:
            refund_params["amount"] = int(request.amount * 100)

        if request.reason:
            refund_params["reason"] = request.reason

        refund = stripe.Refund.create(**refund_params)

        return {
            "refund_id": refund.id,
            "status": refund.status,
            "amount": refund.amount / 100,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process refund: {str(e)}"
        )
