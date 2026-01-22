"""
SalonSync - Salon Management System
FastAPI Application Entry Point
"""

from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.app_settings import get_settings
from app.database import Base, SessionLocal, engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    logger.info("Starting SalonSync...")

    # Validate security settings
    settings.validate_security_settings()

    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

    # Create default admin user if none exists
    try:
        import secrets
        from app.core.security import get_password_hash
        from app.models.user import User, UserRole

        db = SessionLocal()
        admin_exists = db.query(User).filter(User.is_superuser == True).first()
        if not admin_exists:
            default_password = os.environ.get("DEFAULT_ADMIN_PASSWORD")
            if not default_password:
                if settings.is_cloud_deployment:
                    logger.error("DEFAULT_ADMIN_PASSWORD must be set in cloud deployments!")
                    raise ValueError("DEFAULT_ADMIN_PASSWORD required in production")
                default_password = secrets.token_urlsafe(16)
                print(f"\n{'='*60}")
                print(f"GENERATED ADMIN PASSWORD: {default_password}")
                print(f"{'='*60}\n")

            admin_user = User(
                email="admin@salonsync.com",
                hashed_password=get_password_hash(default_password),
                first_name="Admin",
                last_name="User",
                role=UserRole.OWNER,
                is_active=True,
                is_superuser=True,
                is_verified=True,
                must_change_password=True,
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created: admin@salonsync.com")
        else:
            logger.info(f"Admin user already exists: {admin_exists.email}")
        db.close()
    except Exception as e:
        logger.error(f"Failed to create default admin user: {str(e)}")

    yield

    # Shutdown
    logger.info("Shutting down SalonSync...")


# Create FastAPI application
app = FastAPI(
    title="SalonSync - Salon Management System",
    description="""
    Complete salon and spa management system with social media integration.

    ## Features
    - **Appointment Scheduling** - Online booking and calendar management
    - **Client Management** - Client profiles, hair history, and preferences
    - **Point of Sale** - Services and retail product checkout
    - **Staff Management** - Schedules, commissions, and performance
    - **Formula Vault** - Before/after photos with color formulas and techniques
    - **Social Media Publishing** - AI-generated captions, scheduling, analytics
    - **Reporting** - Revenue, staff performance, and client analytics

    ## Differentiators
    - **MediaSets**: Capture complete service records with photos, formulas, and client consent
    - **AI Captions**: Generate professional social media captions with Claude AI
    - **Instagram/TikTok Integration**: Direct publishing to social platforms
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    redirect_slashes=False,
)

# CORS middleware
cors_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

# Add production origins from environment
if settings.FRONTEND_URL:
    cors_origins.append(settings.FRONTEND_URL)

extra_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
extra_origins = [o.strip() for o in extra_origins if o.strip()]
cors_origins.extend(extra_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept", "Origin"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith("/api/auth"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)

    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "path": str(request.url.path),
            }
        )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if settings.DEBUG:
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }
    return {"status": "healthy"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "SalonSync - Salon Management System",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# Import and include API routers
from app.api import auth, salons, stylists, clients, services, appointments
from app.api import media, social, payments, sales, dashboard

# Core authentication
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Salon management (multi-tenant root)
app.include_router(salons.router, prefix="/api", tags=["Salons"])

# Staff & Clients
app.include_router(stylists.router, prefix="/api", tags=["Stylists & Staff"])
app.include_router(clients.router, prefix="/api", tags=["Clients"])

# Services & Appointments
app.include_router(services.router, prefix="/api", tags=["Services"])
app.include_router(appointments.router, prefix="/api", tags=["Appointments"])

# Sales & Dashboard
app.include_router(sales.router, prefix="/api/sales", tags=["Sales & POS"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

# Media & Social (SalonSync differentiators)
app.include_router(media.router, prefix="/api", tags=["Media Sets (Formula Vault)"])
app.include_router(social.router, prefix="/api", tags=["Social Posts"])

# Payments
app.include_router(payments.router, prefix="/api", tags=["Payments & Stripe"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
