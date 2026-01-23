"""
Gift Card model for SalonSync
"""

import enum
import secrets
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class GiftCardStatus(str, enum.Enum):
    """Gift card status"""
    ACTIVE = "active"
    REDEEMED = "redeemed"  # Fully used
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class GiftCardType(str, enum.Enum):
    """Gift card type"""
    DIGITAL = "digital"  # Email delivery
    PHYSICAL = "physical"  # Physical card


class GiftCard(Base):
    """Gift card for salon purchases"""
    __tablename__ = "gift_cards"

    id = Column(Integer, primary_key=True, index=True)

    # Salon Reference
    salon_id = Column(Integer, ForeignKey("salons.id"), nullable=False, index=True)

    # Gift Card Identification
    code = Column(String(20), unique=True, nullable=False, index=True)
    pin = Column(String(10), nullable=True)  # Optional PIN for security

    # Type
    card_type = Column(
        Enum(GiftCardType, values_callable=lambda x: [e.value for e in x]),
        default=GiftCardType.DIGITAL
    )

    # Value
    initial_value = Column(Numeric(10, 2), nullable=False)
    current_balance = Column(Numeric(10, 2), nullable=False)

    # Status
    status = Column(
        Enum(GiftCardStatus, values_callable=lambda x: [e.value for e in x]),
        default=GiftCardStatus.ACTIVE,
        index=True
    )

    # Dates
    purchased_at = Column(DateTime, default=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)  # For physical cards
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    last_used_at = Column(DateTime, nullable=True)

    # Purchaser info
    purchaser_name = Column(String(200), nullable=True)
    purchaser_email = Column(String(255), nullable=True)
    purchaser_phone = Column(String(20), nullable=True)
    purchased_by_client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    # Recipient info
    recipient_name = Column(String(200), nullable=True)
    recipient_email = Column(String(255), nullable=True)
    recipient_phone = Column(String(20), nullable=True)
    recipient_client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    # Personal message
    message = Column(Text, nullable=True)

    # Delivery
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)
    delivery_method = Column(String(20), default="email")  # email, sms, print

    # Design
    design_template = Column(String(50), default="default")

    # Payment reference
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)  # Original purchase

    # Notes
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    salon = relationship("Salon", back_populates="gift_cards")
    purchaser = relationship("Client", foreign_keys=[purchased_by_client_id])
    recipient = relationship("Client", foreign_keys=[recipient_client_id])
    transactions = relationship("GiftCardTransaction", back_populates="gift_card", cascade="all, delete-orphan")

    @staticmethod
    def generate_code() -> str:
        """Generate a unique gift card code."""
        # Format: XXXX-XXXX-XXXX (alphanumeric)
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Excluding confusing chars
        code_parts = []
        for _ in range(3):
            part = "".join(secrets.choice(chars) for _ in range(4))
            code_parts.append(part)
        return "-".join(code_parts)

    @staticmethod
    def generate_pin() -> str:
        """Generate a 4-digit PIN."""
        return "".join(str(secrets.randbelow(10)) for _ in range(4))

    @property
    def is_valid(self) -> bool:
        """Check if gift card is valid for use."""
        if self.status != GiftCardStatus.ACTIVE:
            return False
        if self.current_balance <= 0:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def redeem(self, amount: Decimal) -> Decimal:
        """
        Redeem an amount from the gift card.
        Returns the amount actually redeemed (may be less if insufficient balance).
        """
        if not self.is_valid:
            return Decimal("0")

        redeem_amount = min(amount, self.current_balance)
        self.current_balance -= redeem_amount
        self.last_used_at = datetime.utcnow()

        if self.current_balance <= 0:
            self.status = GiftCardStatus.REDEEMED

        return redeem_amount

    def __repr__(self):
        return f"<GiftCard {self.code} - ${self.current_balance}>"


class GiftCardTransaction(Base):
    """Transaction history for gift cards"""
    __tablename__ = "gift_card_transactions"

    id = Column(Integer, primary_key=True, index=True)

    gift_card_id = Column(Integer, ForeignKey("gift_cards.id"), nullable=False)

    # Transaction type
    transaction_type = Column(String(20), nullable=False)  # purchase, redemption, refund, adjustment

    # Amount (positive for additions, negative for redemptions)
    amount = Column(Numeric(10, 2), nullable=False)

    # Balance after transaction
    balance_after = Column(Numeric(10, 2), nullable=False)

    # Reference
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)  # For redemptions
    description = Column(String(500), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    gift_card = relationship("GiftCard", back_populates="transactions")

    def __repr__(self):
        return f"<GiftCardTransaction {self.id} - {self.transaction_type} ${self.amount}>"
