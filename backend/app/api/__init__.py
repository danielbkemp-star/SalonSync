"""
SalonSync API Routers
"""

from app.api import auth, clients, staff, services, appointments, sales, dashboard

__all__ = [
    "auth",
    "clients",
    "staff",
    "services",
    "appointments",
    "sales",
    "dashboard",
]
