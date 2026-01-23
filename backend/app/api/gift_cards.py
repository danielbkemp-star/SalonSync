"""
SalonSync Gift Card API
Endpoints for gift card management, purchase, and redemption.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.salon import Salon
from app.models.client import Client
from app.models.gift_card import GiftCard, GiftCardTransaction, GiftCardStatus, GiftCardType
from app.services import notification_service

router = APIRouter()


# ==================== SCHEMAS ====================

class GiftCardCreate(BaseModel):
    """Create a new gift card."""
    amount: float = Field(..., gt=0, le=10000)
    card_type: str = "digital"

    # Purchaser info
    purchaser_name: Optional[str] = None
    purchaser_email: Optional[EmailStr] = None
    purchaser_phone: Optional[str] = None

    # Recipient info
    recipient_name: Optional[str] = None
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = None
    message: Optional[str] = None

    # Options
    send_to_recipient: bool = True
    design_template: str = "default"
    expires_in_days: Optional[int] = None  # None = no expiration


class GiftCardResponse(BaseModel):
    """Gift card response."""
    id: int
    code: str
    initial_value: float
    current_balance: float
    status: str
    card_type: str
    purchaser_name: Optional[str]
    recipient_name: Optional[str]
    recipient_email: Optional[str]
    purchased_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    is_valid: bool

    class Config:
        from_attributes = True


class GiftCardBalance(BaseModel):
    """Gift card balance check response."""
    code: str
    current_balance: float
    initial_value: float
    status: str
    is_valid: bool
    expires_at: Optional[datetime]


class GiftCardRedeem(BaseModel):
    """Redeem gift card."""
    code: str
    pin: Optional[str] = None
    amount: float = Field(..., gt=0)


class GiftCardRedeemResponse(BaseModel):
    """Gift card redemption response."""
    redeemed_amount: float
    remaining_balance: float
    status: str


class GiftCardTransactionResponse(BaseModel):
    """Gift card transaction."""
    id: int
    transaction_type: str
    amount: float
    balance_after: float
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== ENDPOINTS ====================

@router.post("/salons/{salon_id}/gift-cards", response_model=GiftCardResponse)
async def create_gift_card(
    salon_id: int,
    gift_card_data: GiftCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new gift card."""
    # Verify salon access
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Generate unique code
    code = GiftCard.generate_code()
    while db.query(GiftCard).filter(GiftCard.code == code).first():
        code = GiftCard.generate_code()

    # Generate PIN for physical cards
    pin = GiftCard.generate_pin() if gift_card_data.card_type == "physical" else None

    # Calculate expiration
    expires_at = None
    if gift_card_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=gift_card_data.expires_in_days)

    # Create gift card
    gift_card = GiftCard(
        salon_id=salon_id,
        code=code,
        pin=pin,
        card_type=GiftCardType(gift_card_data.card_type),
        initial_value=Decimal(str(gift_card_data.amount)),
        current_balance=Decimal(str(gift_card_data.amount)),
        status=GiftCardStatus.ACTIVE,
        purchaser_name=gift_card_data.purchaser_name,
        purchaser_email=gift_card_data.purchaser_email,
        purchaser_phone=gift_card_data.purchaser_phone,
        recipient_name=gift_card_data.recipient_name,
        recipient_email=gift_card_data.recipient_email,
        recipient_phone=gift_card_data.recipient_phone,
        message=gift_card_data.message,
        design_template=gift_card_data.design_template,
        expires_at=expires_at,
        created_by_id=current_user.id,
    )
    db.add(gift_card)

    # Create initial transaction
    transaction = GiftCardTransaction(
        gift_card=gift_card,
        transaction_type="purchase",
        amount=Decimal(str(gift_card_data.amount)),
        balance_after=Decimal(str(gift_card_data.amount)),
        description="Gift card purchased",
        created_by_id=current_user.id,
    )
    db.add(transaction)

    db.commit()
    db.refresh(gift_card)

    # Send to recipient if requested
    if gift_card_data.send_to_recipient and gift_card_data.recipient_email:
        _send_gift_card_email(
            gift_card=gift_card,
            salon=salon,
            to_email=gift_card_data.recipient_email
        )
        gift_card.delivered = True
        gift_card.delivered_at = datetime.utcnow()
        db.commit()

    return gift_card


@router.get("/salons/{salon_id}/gift-cards", response_model=List[GiftCardResponse])
async def list_gift_cards(
    salon_id: int,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all gift cards for a salon."""
    query = db.query(GiftCard).filter(GiftCard.salon_id == salon_id)

    if status:
        query = query.filter(GiftCard.status == status)

    gift_cards = query.order_by(GiftCard.created_at.desc()).offset(skip).limit(limit).all()
    return gift_cards


@router.get("/salons/{salon_id}/gift-cards/{gift_card_id}", response_model=GiftCardResponse)
async def get_gift_card(
    salon_id: int,
    gift_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get gift card details."""
    gift_card = db.query(GiftCard).filter(
        GiftCard.id == gift_card_id,
        GiftCard.salon_id == salon_id
    ).first()

    if not gift_card:
        raise HTTPException(status_code=404, detail="Gift card not found")

    return gift_card


@router.get("/salons/{salon_id}/gift-cards/{gift_card_id}/transactions", response_model=List[GiftCardTransactionResponse])
async def get_gift_card_transactions(
    salon_id: int,
    gift_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get gift card transaction history."""
    gift_card = db.query(GiftCard).filter(
        GiftCard.id == gift_card_id,
        GiftCard.salon_id == salon_id
    ).first()

    if not gift_card:
        raise HTTPException(status_code=404, detail="Gift card not found")

    return gift_card.transactions


# ==================== PUBLIC ENDPOINTS (No auth) ====================

@router.get("/gift-cards/balance", response_model=GiftCardBalance)
async def check_balance(
    code: str,
    pin: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Check gift card balance (public endpoint)."""
    gift_card = db.query(GiftCard).filter(GiftCard.code == code.upper().replace(" ", "")).first()

    if not gift_card:
        raise HTTPException(status_code=404, detail="Gift card not found")

    # Verify PIN if required
    if gift_card.pin and gift_card.pin != pin:
        raise HTTPException(status_code=403, detail="Invalid PIN")

    # Check expiration
    if gift_card.expires_at and datetime.utcnow() > gift_card.expires_at:
        if gift_card.status == GiftCardStatus.ACTIVE:
            gift_card.status = GiftCardStatus.EXPIRED
            db.commit()

    return GiftCardBalance(
        code=gift_card.code,
        current_balance=float(gift_card.current_balance),
        initial_value=float(gift_card.initial_value),
        status=gift_card.status.value,
        is_valid=gift_card.is_valid,
        expires_at=gift_card.expires_at
    )


@router.post("/salons/{salon_id}/gift-cards/redeem", response_model=GiftCardRedeemResponse)
async def redeem_gift_card(
    salon_id: int,
    redemption: GiftCardRedeem,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Redeem a gift card for payment."""
    # Find gift card
    gift_card = db.query(GiftCard).filter(
        GiftCard.code == redemption.code.upper().replace(" ", ""),
        GiftCard.salon_id == salon_id
    ).first()

    if not gift_card:
        raise HTTPException(status_code=404, detail="Gift card not found")

    # Verify PIN if required
    if gift_card.pin and gift_card.pin != redemption.pin:
        raise HTTPException(status_code=403, detail="Invalid PIN")

    # Check if valid
    if not gift_card.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Gift card is {gift_card.status.value}"
        )

    # Redeem amount
    redeem_amount = Decimal(str(redemption.amount))
    actual_redeemed = gift_card.redeem(redeem_amount)

    if actual_redeemed <= 0:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Create transaction
    transaction = GiftCardTransaction(
        gift_card=gift_card,
        transaction_type="redemption",
        amount=-actual_redeemed,  # Negative for redemptions
        balance_after=gift_card.current_balance,
        description=f"Redeemed at POS",
        created_by_id=current_user.id,
    )
    db.add(transaction)

    db.commit()

    return GiftCardRedeemResponse(
        redeemed_amount=float(actual_redeemed),
        remaining_balance=float(gift_card.current_balance),
        status=gift_card.status.value
    )


@router.post("/salons/{salon_id}/gift-cards/{gift_card_id}/cancel")
async def cancel_gift_card(
    salon_id: int,
    gift_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a gift card."""
    gift_card = db.query(GiftCard).filter(
        GiftCard.id == gift_card_id,
        GiftCard.salon_id == salon_id
    ).first()

    if not gift_card:
        raise HTTPException(status_code=404, detail="Gift card not found")

    if gift_card.status != GiftCardStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Gift card is not active")

    gift_card.status = GiftCardStatus.CANCELLED

    # Create transaction
    transaction = GiftCardTransaction(
        gift_card=gift_card,
        transaction_type="cancellation",
        amount=-gift_card.current_balance,
        balance_after=Decimal("0"),
        description="Gift card cancelled",
        created_by_id=current_user.id,
    )
    db.add(transaction)

    gift_card.current_balance = Decimal("0")

    db.commit()

    return {"message": "Gift card cancelled successfully"}


@router.post("/salons/{salon_id}/gift-cards/{gift_card_id}/resend")
async def resend_gift_card(
    salon_id: int,
    gift_card_id: int,
    email: Optional[EmailStr] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resend gift card email to recipient."""
    gift_card = db.query(GiftCard).filter(
        GiftCard.id == gift_card_id,
        GiftCard.salon_id == salon_id
    ).first()

    if not gift_card:
        raise HTTPException(status_code=404, detail="Gift card not found")

    salon = db.query(Salon).filter(Salon.id == salon_id).first()

    recipient_email = email or gift_card.recipient_email
    if not recipient_email:
        raise HTTPException(status_code=400, detail="No recipient email provided")

    _send_gift_card_email(
        gift_card=gift_card,
        salon=salon,
        to_email=recipient_email
    )

    gift_card.delivered = True
    gift_card.delivered_at = datetime.utcnow()
    db.commit()

    return {"message": f"Gift card sent to {recipient_email}"}


# ==================== HELPER FUNCTIONS ====================

def _send_gift_card_email(gift_card: GiftCard, salon: Salon, to_email: str):
    """Send gift card email to recipient."""
    from_name = gift_card.purchaser_name or "Someone special"
    message = gift_card.message or "Enjoy!"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 0 auto; background: white;">
            <div style="background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%); padding: 40px 20px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🎁 You've received a gift!</h1>
            </div>

            <div style="padding: 40px 30px;">
                <p style="font-size: 16px; color: #333;">
                    {from_name} has sent you a gift card to <strong>{salon.name}</strong>!
                </p>

                <div style="background: #f8f5ff; border-radius: 12px; padding: 25px; margin: 25px 0; text-align: center;">
                    <p style="color: #7c3aed; font-size: 14px; margin: 0 0 10px 0;">Gift Card Value</p>
                    <p style="font-size: 48px; font-weight: bold; color: #7c3aed; margin: 0;">
                        ${float(gift_card.initial_value):.2f}
                    </p>
                </div>

                <div style="background: #f9f9f9; border-radius: 12px; padding: 20px; margin: 25px 0; text-align: center;">
                    <p style="color: #666; font-size: 14px; margin: 0 0 10px 0;">Your Gift Card Code</p>
                    <p style="font-size: 24px; font-weight: bold; font-family: monospace; color: #333; margin: 0;">
                        {gift_card.code}
                    </p>
                    {"<p style='font-size: 14px; color: #666; margin: 10px 0 0 0;'>PIN: " + gift_card.pin + "</p>" if gift_card.pin else ""}
                </div>

                {f'<div style="background: #fff; border: 1px solid #eee; border-radius: 12px; padding: 20px; margin: 25px 0;"><p style="color: #666; font-style: italic; margin: 0;">"{message}"</p><p style="color: #999; font-size: 14px; margin: 10px 0 0 0;">- {from_name}</p></div>' if message else ""}

                <div style="text-align: center; margin: 30px 0;">
                    <a href="#" style="display: inline-block; background: #7c3aed; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                        Book Now at {salon.name}
                    </a>
                </div>

                <p style="font-size: 14px; color: #999; text-align: center;">
                    Present this code at checkout to redeem your gift card.
                </p>
            </div>

            <div style="background: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 14px; margin: 0 0 10px 0;">
                    {salon.name}<br>
                    {salon.full_address}
                </p>
                <p style="color: #999; font-size: 12px; margin: 0;">
                    Powered by SalonSync
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    notification_service.send_email(
        to_email=to_email,
        subject=f"🎁 You've received a ${float(gift_card.initial_value):.0f} gift card to {salon.name}!",
        html_content=html_content
    )
