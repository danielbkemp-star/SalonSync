"""
Salon CRUD Tests for SalonSync
"""
import pytest
from fastapi.testclient import TestClient


class TestSalonCreate:
    """Test salon creation"""

    def test_create_salon_success(self, client: TestClient, owner_auth_headers):
        """Test successful salon creation"""
        response = client.post("/api", json={
            "name": "My Test Salon",
            "email": "salon@test.com",
            "phone": "555-123-4567",
            "address_line1": "123 Main St",
            "city": "Portland",
            "state": "OR",
            "zip_code": "97201"
        }, headers=owner_auth_headers)
        assert response.status_code == 201, f"Create failed: {response.json()}"
        data = response.json()
        assert data["name"] == "My Test Salon"
        assert data["slug"] is not None
        assert data["subscription_tier"] == "free"
        assert data["is_active"] == True

    def test_create_salon_minimal(self, client: TestClient, owner_auth_headers):
        """Test salon creation with minimal fields"""
        response = client.post("/api", json={
            "name": "Minimal Salon"
        }, headers=owner_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Salon"
        assert data["slug"] == "minimal-salon"

    def test_create_salon_duplicate_slug(self, client: TestClient, owner_auth_headers):
        """Test salon creation with duplicate slug fails"""
        # Create first salon
        client.post("/api", json={
            "name": "Unique Salon",
            "slug": "unique-salon"
        }, headers=owner_auth_headers)

        # Try to create another with same slug
        response = client.post("/api", json={
            "name": "Another Salon",
            "slug": "unique-salon"
        }, headers=owner_auth_headers)
        assert response.status_code == 400

    def test_create_salon_without_auth(self, client: TestClient):
        """Test salon creation requires authentication"""
        response = client.post("/api", json={
            "name": "No Auth Salon"
        })
        assert response.status_code == 401


class TestSalonRead:
    """Test salon retrieval"""

    def test_list_salons(self, client: TestClient, owner_auth_headers, test_salon):
        """Test listing salons"""
        response = client.get("/api", headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_get_salon_by_id(self, client: TestClient, owner_auth_headers, test_salon):
        """Test getting salon by ID"""
        response = client.get(f"/api/{test_salon.id}", headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_salon.id
        assert data["name"] == test_salon.name

    def test_get_nonexistent_salon(self, client: TestClient, owner_auth_headers):
        """Test getting non-existent salon returns 404"""
        response = client.get("/api/99999", headers=owner_auth_headers)
        assert response.status_code == 404

    def test_get_salon_without_access(self, client: TestClient, auth_headers, test_salon):
        """Test user without access cannot get salon"""
        response = client.get(f"/api/{test_salon.id}", headers=auth_headers)
        assert response.status_code == 403


class TestSalonUpdate:
    """Test salon updates"""

    def test_update_salon_success(self, client: TestClient, owner_auth_headers, test_salon):
        """Test successful salon update"""
        response = client.put(f"/api/{test_salon.id}", json={
            "name": "Updated Salon Name",
            "phone": "555-999-8888"
        }, headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Salon Name"

    def test_update_salon_settings(self, client: TestClient, owner_auth_headers, test_salon):
        """Test updating salon settings"""
        response = client.put(f"/api/{test_salon.id}/settings", json={
            "booking_lead_time_hours": 4,
            "cancellation_policy_hours": 48,
            "deposit_required": True,
            "deposit_percentage": 25.0
        }, headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["booking_lead_time_hours"] == 4
        assert data["deposit_required"] == True


class TestSalonStats:
    """Test salon statistics"""

    def test_get_salon_stats(self, client: TestClient, owner_auth_headers, test_salon):
        """Test getting salon statistics"""
        response = client.get(f"/api/{test_salon.id}/stats", headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_clients" in data
        assert "total_staff" in data
        assert "total_revenue_today" in data


class TestSalonDelete:
    """Test salon deletion"""

    def test_delete_salon(self, client: TestClient, owner_auth_headers, db):
        """Test salon soft delete"""
        from app.models.salon import Salon
        from app.models.staff import Staff

        # Create a salon to delete
        salon = Salon(
            name="To Delete",
            slug="to-delete",
            owner_id=1
        )
        db.add(salon)
        db.commit()
        db.refresh(salon)

        # Create staff profile for owner
        staff = Staff(
            salon_id=salon.id,
            user_id=1,  # owner user id
            title="Owner",
            status="active"
        )
        db.add(staff)
        db.commit()

        response = client.delete(f"/api/{salon.id}", headers=owner_auth_headers)
        assert response.status_code == 200

        # Verify soft delete
        db.refresh(salon)
        assert salon.is_active == False
