"""
Sales & POS API for SalonSync
"""

from datetime import datetime, date
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, require_staff
from app.database import get_db
from app.models.user import User
from app.models.sale import Sale, SaleItem, PaymentMethod, PaymentStatus

router = APIRouter()


class SaleItemCreate(BaseModel):
    item_type: str  # service, product, tip
    service_id: Optional[int] = None
    product_id: Optional[int] = None
    staff_id: Optional[int] = None
    name: str
    quantity: int = 1
    unit_price: float
    discount: float = 0


class SaleCreate(BaseModel):
    client_id: Optional[int] = None
    staff_id: Optional[int] = None
    appointment_id: Optional[int] = None
    items: List[SaleItemCreate]
    payment_method: str = "card"
    tip_amount: float = 0
    discount_amount: float = 0
    discount_code: Optional[str] = None
    discount_reason: Optional[str] = None
    notes: Optional[str] = None


class SaleResponse(BaseModel):
    id: int
    client_id: Optional[int]
    staff_id: Optional[int]
    subtotal: float
    tax_amount: float
    discount_amount: float
    tip_amount: float
    total: float
    payment_method: str
    payment_status: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SaleResponse])
async def list_sales(
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    client_id: Optional[int] = None,
    staff_id: Optional[int] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
):
    """List sales with filters."""
    query = db.query(Sale)

    if start_date:
        query = query.filter(Sale.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.filter(Sale.created_at <= datetime.combine(end_date, datetime.max.time()))

    if client_id:
        query = query.filter(Sale.client_id == client_id)

    if staff_id:
        query = query.filter(Sale.staff_id == staff_id)

    query = query.order_by(Sale.created_at.desc())
    return query.offset(offset).limit(limit).all()


@router.get("/today/summary")
async def get_today_summary(
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
):
    """Get today's sales summary."""
    from sqlalchemy import func

    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    result = db.query(
        func.count(Sale.id).label("transaction_count"),
        func.sum(Sale.total).label("total_revenue"),
        func.sum(Sale.tip_amount).label("total_tips"),
        func.sum(Sale.discount_amount).label("total_discounts"),
    ).filter(
        Sale.created_at >= today_start,
        Sale.created_at <= today_end,
        Sale.payment_status == PaymentStatus.COMPLETED,
    ).first()

    return {
        "date": today.isoformat(),
        "transaction_count": result.transaction_count or 0,
        "total_revenue": float(result.total_revenue or 0),
        "total_tips": float(result.total_tips or 0),
        "total_discounts": float(result.total_discounts or 0),
    }


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: int,
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
):
    """Get a specific sale."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    return sale


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_data: SaleCreate,
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
):
    """Process a new sale."""
    # Calculate totals
    subtotal = 0
    for item in sale_data.items:
        item_total = (item.unit_price * item.quantity) - item.discount
        subtotal += item_total

    # TODO: Make tax rate configurable
    tax_rate = 0.0  # Oregon has no sales tax
    tax_amount = subtotal * tax_rate

    total = subtotal + tax_amount - sale_data.discount_amount + sale_data.tip_amount

    # Create sale
    sale = Sale(
        client_id=sale_data.client_id,
        staff_id=sale_data.staff_id,
        appointment_id=sale_data.appointment_id,
        subtotal=subtotal,
        tax_amount=tax_amount,
        discount_amount=sale_data.discount_amount,
        tip_amount=sale_data.tip_amount,
        total=total,
        payment_method=PaymentMethod(sale_data.payment_method),
        payment_status=PaymentStatus.COMPLETED,
        discount_code=sale_data.discount_code,
        discount_reason=sale_data.discount_reason,
        notes=sale_data.notes,
        created_by_id=current_user.id,
    )
    db.add(sale)
    db.flush()

    # Add items
    for item_data in sale_data.items:
        item_total = (item_data.unit_price * item_data.quantity) - item_data.discount
        item = SaleItem(
            sale_id=sale.id,
            item_type=item_data.item_type,
            service_id=item_data.service_id,
            product_id=item_data.product_id,
            staff_id=item_data.staff_id,
            name=item_data.name,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            discount=item_data.discount,
            total=item_total,
        )
        db.add(item)

    # Update client stats if client provided
    if sale_data.client_id:
        from app.models.client import Client
        client = db.query(Client).filter(Client.id == sale_data.client_id).first()
        if client:
            client.visit_count += 1
            client.total_spent = float(client.total_spent) + float(total)
            client.last_visit = datetime.utcnow()

    db.commit()
    db.refresh(sale)
    return sale


@router.post("/{sale_id}/refund", response_model=SaleResponse)
async def refund_sale(
    sale_id: int,
    amount: Optional[float] = None,
    reason: Optional[str] = None,
    current_user: Annotated[User, Depends(require_staff)],
    db: Session = Depends(get_db),
):
    """Process a refund."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )

    refund_amount = amount if amount is not None else float(sale.total)

    if refund_amount > float(sale.total) - float(sale.refund_amount):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund amount exceeds remaining balance"
        )

    sale.refund_amount = float(sale.refund_amount) + refund_amount
    sale.refunded_at = datetime.utcnow()
    sale.refund_reason = reason

    if sale.refund_amount >= float(sale.total):
        sale.payment_status = PaymentStatus.REFUNDED
    else:
        sale.payment_status = PaymentStatus.PARTIALLY_REFUNDED

    db.commit()
    db.refresh(sale)
    return sale
