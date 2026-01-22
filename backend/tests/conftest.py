"""
Test configuration for SalonSync
"""
import os
import pytest
from typing import Generator

# Set test environment variables BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test_salonsync.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DEBUG"] = "true"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash, create_access_token

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_salonsync.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database tables before tests run."""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup after all tests
    Base.metadata.drop_all(bind=engine)
    # Remove test database file
    import os
    if os.path.exists("./test_salonsync.db"):
        os.remove("./test_salonsync.db")


@pytest.fixture
def db() -> Generator:
    """Get test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Clean up all data after each test
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()


@pytest.fixture
def client(db) -> Generator:
    """Get test client with database override."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db) -> User:
    """Create a test user."""
    user = User(
        email="testuser@salonsync.com",
        hashed_password=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="User",
        role=UserRole.CLIENT,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_owner(db) -> User:
    """Create a test owner user."""
    user = User(
        email="owner@salonsync.com",
        hashed_password=get_password_hash("ownerpassword123"),
        first_name="Test",
        last_name="Owner",
        role=UserRole.OWNER,
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Get authentication headers for test user."""
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner_auth_headers(test_owner) -> dict:
    """Get authentication headers for owner user."""
    token = create_access_token(subject=str(test_owner.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_salon(db, test_owner):
    """Create a test salon."""
    from app.models.salon import Salon
    from app.models.staff import Staff

    salon = Salon(
        name="Test Salon",
        slug="test-salon",
        owner_id=test_owner.id,
        email="salon@test.com",
        phone="555-123-4567",
        address_line1="123 Test St",
        city="Portland",
        state="OR",
        zip_code="97201",
        is_active=True,
    )
    db.add(salon)
    db.commit()
    db.refresh(salon)

    # Create staff profile for owner
    staff = Staff(
        salon_id=salon.id,
        user_id=test_owner.id,
        title="Owner",
        status="active",
    )
    db.add(staff)
    db.commit()

    return salon
