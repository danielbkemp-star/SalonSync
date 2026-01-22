"""
Dashboard API for SalonSync
"""

from datetime import datetime, date, timedelta
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_staff_role
from app.database import get_db
from app.models.user import User
from app.models.appointment import Appointment, AppointmentStatus
from app.models.sale import Sale, PaymentStatus
from app.models.client import Client

router = APIRouter()


class DashboardMetrics(BaseModel):
    today_appointments: int
    today_revenue: float
    week_revenue: float
    month_revenue: float
    new_clients_this_month: int
    total_active_clients: int
    upcoming_appointments: int
    cancelled_today: int


class AppointmentSummary(BaseModel):
    id: int
    client_name: str
    staff_name: str
    start_time: datetime
    duration_mins: int
    status: str
    services: List[str]


class RevenueData(BaseModel):
    date: str
    revenue: float
    transactions: int


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
):
    """Get key metrics for the dashboard."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Today's appointments
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    today_appts = db.query(func.count(Appointment.id)).filter(
        Appointment.start_time >= today_start,
        Appointment.start_time <= today_end,
        Appointment.status != AppointmentStatus.CANCELLED,
    ).scalar() or 0

    # Today's revenue
    today_revenue = db.query(func.sum(Sale.total)).filter(
        Sale.created_at >= today_start,
        Sale.created_at <= today_end,
        Sale.payment_status == PaymentStatus.COMPLETED,
    ).scalar() or 0

    # Week revenue
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    week_revenue = db.query(func.sum(Sale.total)).filter(
        Sale.created_at >= week_start_dt,
        Sale.payment_status == PaymentStatus.COMPLETED,
    ).scalar() or 0

    # Month revenue
    month_start_dt = datetime.combine(month_start, datetime.min.time())
    month_revenue = db.query(func.sum(Sale.total)).filter(
        Sale.created_at >= month_start_dt,
        Sale.payment_status == PaymentStatus.COMPLETED,
    ).scalar() or 0

    # New clients this month
    new_clients = db.query(func.count(Client.id)).filter(
        Client.created_at >= month_start_dt,
    ).scalar() or 0

    # Total active clients
    total_clients = db.query(func.count(Client.id)).filter(
        Client.is_active == True,
    ).scalar() or 0

    # Upcoming appointments (next 2 hours)
    now = datetime.utcnow()
    two_hours = now + timedelta(hours=2)
    upcoming = db.query(func.count(Appointment.id)).filter(
        Appointment.start_time >= now,
        Appointment.start_time <= two_hours,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
    ).scalar() or 0

    # Cancelled today
    cancelled_today = db.query(func.count(Appointment.id)).filter(
        Appointment.cancelled_at >= today_start,
        Appointment.cancelled_at <= today_end,
    ).scalar() or 0

    return DashboardMetrics(
        today_appointments=today_appts,
        today_revenue=float(today_revenue),
        week_revenue=float(week_revenue),
        month_revenue=float(month_revenue),
        new_clients_this_month=new_clients,
        total_active_clients=total_clients,
        upcoming_appointments=upcoming,
        cancelled_today=cancelled_today,
    )


@router.get("/appointments/upcoming")
async def get_upcoming_appointments(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
    limit: int = Query(10, le=50),
):
    """Get upcoming appointments for dashboard."""
    from sqlalchemy.orm import joinedload

    now = datetime.utcnow()
    appointments = db.query(Appointment).options(
        joinedload(Appointment.client),
        joinedload(Appointment.staff).joinedload("user"),
        joinedload(Appointment.services).joinedload("service"),
    ).filter(
        Appointment.start_time >= now,
        Appointment.status.in_([
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CHECKED_IN,
        ]),
    ).order_by(Appointment.start_time).limit(limit).all()

    return [
        {
            "id": appt.id,
            "client_name": appt.client.full_name if appt.client else "Walk-in",
            "staff_name": appt.staff.full_name if appt.staff else "Unassigned",
            "start_time": appt.start_time.isoformat(),
            "duration_mins": appt.duration_mins,
            "status": appt.status.value,
            "services": [s.service.name for s in appt.services],
        }
        for appt in appointments
    ]


@router.get("/revenue/daily")
async def get_daily_revenue(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
    days: int = Query(7, le=90),
):
    """Get daily revenue for the past N days."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    results = db.query(
        func.date(Sale.created_at).label("date"),
        func.sum(Sale.total).label("revenue"),
        func.count(Sale.id).label("transactions"),
    ).filter(
        Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
        Sale.payment_status == PaymentStatus.COMPLETED,
    ).group_by(
        func.date(Sale.created_at)
    ).order_by("date").all()

    # Fill in missing dates with zeros
    revenue_by_date = {str(r.date): {"revenue": float(r.revenue), "transactions": r.transactions} for r in results}

    data = []
    current = start_date
    while current <= end_date:
        date_str = current.isoformat()
        if date_str in revenue_by_date:
            data.append({
                "date": date_str,
                "revenue": revenue_by_date[date_str]["revenue"],
                "transactions": revenue_by_date[date_str]["transactions"],
            })
        else:
            data.append({
                "date": date_str,
                "revenue": 0,
                "transactions": 0,
            })
        current += timedelta(days=1)

    return data


@router.get("/needs-attention")
async def get_needs_attention(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
):
    """Get items that need attention."""
    now = datetime.utcnow()
    items = []

    # Appointments in next 15 minutes not checked in
    fifteen_mins = now + timedelta(minutes=15)
    soon_appts = db.query(Appointment).filter(
        Appointment.start_time >= now,
        Appointment.start_time <= fifteen_mins,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
    ).count()

    if soon_appts > 0:
        items.append({
            "type": "warning",
            "title": f"{soon_appts} appointment(s) starting soon",
            "description": "Client not checked in yet",
            "action_url": "/appointments",
        })

    # Low inventory products
    from app.models.sale import Product
    low_inventory = db.query(Product).filter(
        Product.is_active == True,
        Product.quantity_on_hand <= Product.reorder_point,
    ).count()

    if low_inventory > 0:
        items.append({
            "type": "info",
            "title": f"{low_inventory} product(s) low on stock",
            "description": "Consider reordering",
            "action_url": "/inventory",
        })

    # Recent no-shows
    today = date.today()
    week_ago = today - timedelta(days=7)
    no_shows = db.query(Appointment).filter(
        Appointment.status == AppointmentStatus.NO_SHOW,
        Appointment.start_time >= datetime.combine(week_ago, datetime.min.time()),
    ).count()

    if no_shows > 0:
        items.append({
            "type": "alert",
            "title": f"{no_shows} no-show(s) this week",
            "description": "Review client policies",
            "action_url": "/reports/no-shows",
        })

    return items
