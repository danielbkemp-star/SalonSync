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


# ==================== ADVANCED ANALYTICS ====================

class StaffPerformance(BaseModel):
    staff_id: int
    staff_name: str
    avatar_initials: str
    total_revenue: float
    appointment_count: int
    avg_ticket: float
    utilization_pct: float
    rating: Optional[float] = None
    return_client_pct: float


class ServicePerformance(BaseModel):
    service_id: int
    service_name: str
    category: Optional[str]
    revenue: float
    booking_count: int
    avg_price: float
    growth_pct: float


class ClientInsights(BaseModel):
    total_clients: int
    new_clients: int
    returning_clients: int
    retention_rate: float
    avg_visits_per_client: float
    top_clients: List[dict]
    churn_risk: int


class HourlyPattern(BaseModel):
    hour: int
    appointment_count: int
    revenue: float


class DayPattern(BaseModel):
    day: int
    day_name: str
    appointment_count: int
    revenue: float


@router.get("/analytics/staff-performance", response_model=List[StaffPerformance])
async def get_staff_performance(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
    days: int = Query(30, le=365),
):
    """Get staff performance metrics."""
    from app.models.staff import Staff
    from app.models.service import Service
    from app.models.appointment import AppointmentService

    start_date = datetime.utcnow() - timedelta(days=days)

    # Get all staff with their appointments and sales
    staff_members = db.query(Staff).filter(Staff.is_active == True).all()

    results = []
    for staff in staff_members:
        # Count appointments
        appointments = db.query(Appointment).filter(
            Appointment.staff_id == staff.id,
            Appointment.start_time >= start_date,
            Appointment.status == AppointmentStatus.COMPLETED,
        ).all()

        appt_count = len(appointments)

        # Calculate revenue from completed appointments
        total_revenue = 0.0
        for appt in appointments:
            for appt_svc in appt.services:
                total_revenue += float(appt_svc.price)

        avg_ticket = total_revenue / appt_count if appt_count > 0 else 0

        # Calculate utilization (assuming 8 hour workday, 5 days a week)
        work_hours = days * (8 * 5 / 7)  # Approximate work hours
        total_appt_hours = sum(a.duration_mins for a in appointments) / 60
        utilization = (total_appt_hours / work_hours * 100) if work_hours > 0 else 0

        # Return client percentage
        client_ids = [a.client_id for a in appointments if a.client_id]
        unique_clients = len(set(client_ids))
        returning = len(client_ids) - unique_clients
        return_pct = (returning / len(client_ids) * 100) if client_ids else 0

        results.append(StaffPerformance(
            staff_id=staff.id,
            staff_name=staff.full_name,
            avatar_initials=''.join(n[0].upper() for n in staff.full_name.split()[:2]),
            total_revenue=round(total_revenue, 2),
            appointment_count=appt_count,
            avg_ticket=round(avg_ticket, 2),
            utilization_pct=round(min(utilization, 100), 1),
            rating=4.5 + (hash(staff.id) % 5) / 10,  # Placeholder until review system
            return_client_pct=round(return_pct, 1),
        ))

    # Sort by revenue descending
    results.sort(key=lambda x: x.total_revenue, reverse=True)
    return results


@router.get("/analytics/service-performance", response_model=List[ServicePerformance])
async def get_service_performance(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
    days: int = Query(30, le=365),
):
    """Get service performance metrics."""
    from app.models.service import Service
    from app.models.appointment import AppointmentService

    start_date = datetime.utcnow() - timedelta(days=days)
    prev_start = start_date - timedelta(days=days)

    services = db.query(Service).filter(Service.is_active == True).all()

    results = []
    for svc in services:
        # Current period
        current_bookings = db.query(AppointmentService).join(Appointment).filter(
            AppointmentService.service_id == svc.id,
            Appointment.start_time >= start_date,
            Appointment.status == AppointmentStatus.COMPLETED,
        ).all()

        current_count = len(current_bookings)
        current_revenue = sum(float(b.price) for b in current_bookings)

        # Previous period for growth calculation
        prev_bookings = db.query(AppointmentService).join(Appointment).filter(
            AppointmentService.service_id == svc.id,
            Appointment.start_time >= prev_start,
            Appointment.start_time < start_date,
            Appointment.status == AppointmentStatus.COMPLETED,
        ).all()

        prev_revenue = sum(float(b.price) for b in prev_bookings)
        growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0

        if current_count > 0:
            results.append(ServicePerformance(
                service_id=svc.id,
                service_name=svc.name,
                category=svc.category,
                revenue=round(current_revenue, 2),
                booking_count=current_count,
                avg_price=round(current_revenue / current_count, 2),
                growth_pct=round(growth, 1),
            ))

    # Sort by revenue descending
    results.sort(key=lambda x: x.revenue, reverse=True)
    return results[:10]


@router.get("/analytics/client-insights", response_model=ClientInsights)
async def get_client_insights(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
    days: int = Query(30, le=365),
):
    """Get client analytics and insights."""
    start_date = datetime.utcnow() - timedelta(days=days)
    prev_period = start_date - timedelta(days=days)

    # Total active clients
    total = db.query(func.count(Client.id)).filter(Client.is_active == True).scalar() or 0

    # New clients in period
    new_clients = db.query(func.count(Client.id)).filter(
        Client.created_at >= start_date,
    ).scalar() or 0

    # Clients with appointments in current period
    current_clients = db.query(func.count(func.distinct(Appointment.client_id))).filter(
        Appointment.start_time >= start_date,
        Appointment.status == AppointmentStatus.COMPLETED,
        Appointment.client_id.isnot(None),
    ).scalar() or 0

    # Clients with appointments in previous period who also had appointments this period
    prev_clients = db.query(Appointment.client_id).filter(
        Appointment.start_time >= prev_period,
        Appointment.start_time < start_date,
        Appointment.status == AppointmentStatus.COMPLETED,
        Appointment.client_id.isnot(None),
    ).distinct().subquery()

    retained = db.query(func.count(func.distinct(Appointment.client_id))).filter(
        Appointment.start_time >= start_date,
        Appointment.status == AppointmentStatus.COMPLETED,
        Appointment.client_id.in_(db.query(prev_clients.c.client_id)),
    ).scalar() or 0

    prev_count = db.query(func.count()).select_from(prev_clients).scalar() or 0
    retention_rate = (retained / prev_count * 100) if prev_count > 0 else 0

    returning = current_clients - new_clients

    # Average visits per client
    total_visits = db.query(func.count(Appointment.id)).filter(
        Appointment.start_time >= start_date,
        Appointment.status == AppointmentStatus.COMPLETED,
        Appointment.client_id.isnot(None),
    ).scalar() or 0
    avg_visits = total_visits / current_clients if current_clients > 0 else 0

    # Top clients by spend
    top_clients_data = db.query(
        Client.id,
        Client.first_name,
        Client.last_name,
        func.count(Appointment.id).label("visits"),
        func.sum(Sale.total).label("total_spent"),
    ).outerjoin(Appointment, Client.id == Appointment.client_id).outerjoin(
        Sale, Appointment.id == Sale.appointment_id
    ).filter(
        Appointment.start_time >= start_date,
        Appointment.status == AppointmentStatus.COMPLETED,
    ).group_by(Client.id).order_by(func.sum(Sale.total).desc()).limit(5).all()

    top_clients = [
        {
            "id": c.id,
            "name": f"{c.first_name} {c.last_name}",
            "visits": c.visits,
            "total_spent": float(c.total_spent or 0),
        }
        for c in top_clients_data
    ]

    # Clients at churn risk (no visit in 60+ days but were active before)
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)
    churn_risk = db.query(func.count(func.distinct(Appointment.client_id))).filter(
        Appointment.start_time < sixty_days_ago,
        Appointment.status == AppointmentStatus.COMPLETED,
        Appointment.client_id.isnot(None),
        ~Appointment.client_id.in_(
            db.query(Appointment.client_id).filter(
                Appointment.start_time >= sixty_days_ago,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
        )
    ).scalar() or 0

    return ClientInsights(
        total_clients=total,
        new_clients=new_clients,
        returning_clients=max(0, returning),
        retention_rate=round(retention_rate, 1),
        avg_visits_per_client=round(avg_visits, 2),
        top_clients=top_clients,
        churn_risk=churn_risk,
    )


@router.get("/analytics/hourly-patterns", response_model=List[HourlyPattern])
async def get_hourly_patterns(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
    days: int = Query(30, le=365),
):
    """Get appointment patterns by hour of day."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get all completed appointments in period
    appointments = db.query(Appointment).filter(
        Appointment.start_time >= start_date,
        Appointment.status == AppointmentStatus.COMPLETED,
    ).all()

    # Aggregate by hour
    hourly = {i: {"count": 0, "revenue": 0.0} for i in range(24)}
    for appt in appointments:
        hour = appt.start_time.hour
        hourly[hour]["count"] += 1
        for svc in appt.services:
            hourly[hour]["revenue"] += float(svc.price)

    return [
        HourlyPattern(
            hour=hour,
            appointment_count=data["count"],
            revenue=round(data["revenue"], 2),
        )
        for hour, data in hourly.items()
    ]


@router.get("/analytics/daily-patterns", response_model=List[DayPattern])
async def get_daily_patterns(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
    days: int = Query(30, le=365),
):
    """Get appointment patterns by day of week."""
    start_date = datetime.utcnow() - timedelta(days=days)
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    appointments = db.query(Appointment).filter(
        Appointment.start_time >= start_date,
        Appointment.status == AppointmentStatus.COMPLETED,
    ).all()

    daily = {i: {"count": 0, "revenue": 0.0} for i in range(7)}
    for appt in appointments:
        day = appt.start_time.weekday()
        daily[day]["count"] += 1
        for svc in appt.services:
            daily[day]["revenue"] += float(svc.price)

    return [
        DayPattern(
            day=day,
            day_name=day_names[day],
            appointment_count=data["count"],
            revenue=round(data["revenue"], 2),
        )
        for day, data in daily.items()
    ]


@router.get("/analytics/appointments/by-status")
async def get_appointments_by_status(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
    days: int = Query(30, le=365),
):
    """Get appointment breakdown by status."""
    start_date = datetime.utcnow() - timedelta(days=days)

    results = db.query(
        Appointment.status,
        func.count(Appointment.id).label("count"),
    ).filter(
        Appointment.start_time >= start_date,
    ).group_by(Appointment.status).all()

    return [
        {"status": r.status.value, "count": r.count}
        for r in results
    ]


@router.get("/analytics/revenue-comparison")
async def get_revenue_comparison(
    current_user: Annotated[User, Depends(require_staff_role)],
    db: Session = Depends(get_db),
    days: int = Query(30, le=365),
):
    """Get revenue comparison between current and previous period."""
    now = datetime.utcnow()
    current_start = now - timedelta(days=days)
    prev_start = current_start - timedelta(days=days)

    # Current period
    current_revenue = db.query(func.sum(Sale.total)).filter(
        Sale.created_at >= current_start,
        Sale.payment_status == PaymentStatus.COMPLETED,
    ).scalar() or 0

    current_count = db.query(func.count(Sale.id)).filter(
        Sale.created_at >= current_start,
        Sale.payment_status == PaymentStatus.COMPLETED,
    ).scalar() or 0

    # Previous period
    prev_revenue = db.query(func.sum(Sale.total)).filter(
        Sale.created_at >= prev_start,
        Sale.created_at < current_start,
        Sale.payment_status == PaymentStatus.COMPLETED,
    ).scalar() or 0

    prev_count = db.query(func.count(Sale.id)).filter(
        Sale.created_at >= prev_start,
        Sale.created_at < current_start,
        Sale.payment_status == PaymentStatus.COMPLETED,
    ).scalar() or 0

    revenue_change = ((float(current_revenue) - float(prev_revenue)) / float(prev_revenue) * 100) if prev_revenue > 0 else 0
    count_change = ((current_count - prev_count) / prev_count * 100) if prev_count > 0 else 0

    return {
        "current_period": {
            "revenue": float(current_revenue),
            "transactions": current_count,
            "avg_ticket": float(current_revenue) / current_count if current_count > 0 else 0,
        },
        "previous_period": {
            "revenue": float(prev_revenue),
            "transactions": prev_count,
            "avg_ticket": float(prev_revenue) / prev_count if prev_count > 0 else 0,
        },
        "changes": {
            "revenue_pct": round(revenue_change, 1),
            "transactions_pct": round(count_change, 1),
        }
    }
