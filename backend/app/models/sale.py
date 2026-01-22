"""
Sale and Product models for SalonSync
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentMethod(str, enum.Enum):
    """Payment methods"""
    CASH = "cash"
    CARD = "card"
    GIFT_CARD = "gift_card"
    LOYALTY_POINTS = "loyalty_points"
    CHECK = "check"
    SPLIT = "split"


class PaymentStatus(str, enum.Enum):
    """Payment status"""
    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    FAILED = "failed"


class Product(Base):
    """Retail product"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    sku = Column(String(50), unique=True, nullable=True)
    barcode = Column(String(50), unique=True, nullable=True)

    # Pricing
    cost = Column(Numeric(10, 2), nullable=True)  # Our cost
    price = Column(Numeric(10, 2), nullable=False)  # Retail price
    msrp = Column(Numeric(10, 2), nullable=True)  # Manufacturer suggested

    # Inventory
    quantity_on_hand = Column(Integer, default=0)
    reorder_point = Column(Integer, default=5)
    reorder_quantity = Column(Integer, default=10)

    # Commission
    commission_type = Column(String(20), default="percentage")
    commission_value = Column(Numeric(10, 2), nullable=True)

    # Display
    is_active = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)
    display_order = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sale_items = relationship("SaleItem", back_populates="product")

    def __repr__(self):
        return f"<Product {self.id} - {self.name}>"


class Sale(Base):
    """Point of sale transaction"""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)

    # References
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)  # Who processed the sale
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    # Totals
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    tip_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total = Column(Numeric(10, 2), nullable=False, default=0)

    # Payment
    payment_method = Column(
        Enum(PaymentMethod, values_callable=lambda x: [e.value for e in x]),
        default=PaymentMethod.CARD
    )
    payment_status = Column(
        Enum(PaymentStatus, values_callable=lambda x: [e.value for e in x]),
        default=PaymentStatus.COMPLETED
    )
    payment_details = Column(JSON, nullable=True)  # Card last 4, transaction ID, etc.

    # Discount
    discount_code = Column(String(50), nullable=True)
    discount_reason = Column(String(200), nullable=True)

    # Gift Card / Loyalty
    gift_card_id = Column(Integer, nullable=True)
    loyalty_points_used = Column(Integer, default=0)
    loyalty_points_earned = Column(Integer, default=0)

    # Refund
    refund_amount = Column(Numeric(10, 2), default=0)
    refunded_at = Column(DateTime, nullable=True)
    refund_reason = Column(Text, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    client = relationship("Client", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Sale {self.id} - ${self.total}>"


class SaleItem(Base):
    """Individual item in a sale"""
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)

    # Item Type
    item_type = Column(String(20), nullable=False)  # service, product, tip

    # References (one will be set based on item_type)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)  # Who performed service/sold item

    # Item Details (snapshot at time of sale)
    name = Column(String(200), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)

    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

    def __repr__(self):
        return f"<SaleItem {self.id} - {self.name}>"
