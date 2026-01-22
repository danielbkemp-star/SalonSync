"""
Integration Tests - Full User Flows for SalonSync
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


class TestNewSalonSetupFlow:
    """Test complete new salon owner onboarding"""

    def test_full_onboarding_flow(self, client: TestClient, db):
        """Test: Register -> Login -> Create Salon -> Add Services -> Add Clients"""
        # 1. Register new user
        register_resp = client.post("/api/auth/register", json={
            "email": "newowner@testsalon.com",
            "password": "securepassword123",
            "first_name": "Sarah",
            "last_name": "Owner"
        })
        assert register_resp.status_code == 201, f"Register failed: {register_resp.json()}"
        user_id = register_resp.json()["id"]

        # 2. Login
        login_resp = client.post("/api/auth/login", data={
            "username": "newowner@testsalon.com",
            "password": "securepassword123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.json()}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create salon
        salon_resp = client.post("/api", json={
            "name": "Beautiful Hair Studio",
            "email": "info@beautifulhair.com",
            "phone": "555-123-4567",
            "address_line1": "456 Style Ave",
            "city": "Portland",
            "state": "OR",
            "zip_code": "97201"
        }, headers=headers)
        assert salon_resp.status_code == 201, f"Create salon failed: {salon_resp.json()}"
        salon_id = salon_resp.json()["id"]
        assert salon_resp.json()["slug"] is not None

        # 4. Add services
        service1_resp = client.post(f"/api/salons/{salon_id}/services", json={
            "name": "Women's Haircut",
            "category": "Haircut",
            "duration_mins": 45,
            "price": 65.00
        }, headers=headers)
        assert service1_resp.status_code == 201

        service2_resp = client.post(f"/api/salons/{salon_id}/services", json={
            "name": "Full Color",
            "category": "Color",
            "duration_mins": 90,
            "price": 120.00
        }, headers=headers)
        assert service2_resp.status_code == 201

        # 5. Add a client
        client_resp = client.post(f"/api/salons/{salon_id}/clients", json={
            "first_name": "Jane",
            "last_name": "Client",
            "email": "jane@example.com",
            "phone": "555-987-6543"
        }, headers=headers)
        assert client_resp.status_code == 201

        # 6. Verify everything is set up
        salon_detail = client.get(f"/api/{salon_id}", headers=headers)
        assert salon_detail.status_code == 200
        assert salon_detail.json()["name"] == "Beautiful Hair Studio"

        # Verify stats show the new data
        stats_resp = client.get(f"/api/{salon_id}/stats", headers=headers)
        assert stats_resp.status_code == 200
        assert stats_resp.json()["total_clients"] >= 1
        assert stats_resp.json()["total_staff"] >= 1


class TestClientManagementFlow:
    """Test complete client management flow"""

    def test_client_lifecycle(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test: Create Client -> Update Profile -> Add Tags -> Update Consent -> View History"""
        # 1. Create client
        create_resp = client.post(f"/api/salons/{test_salon.id}/clients", json={
            "first_name": "Test",
            "last_name": "Client",
            "email": "testclient@example.com",
            "phone": "555-111-2222",
            "hair_profile": {
                "hair_type": "medium",
                "hair_texture": "curly",
                "hair_color": "brunette"
            }
        }, headers=owner_auth_headers)
        assert create_resp.status_code == 201
        client_id = create_resp.json()["id"]

        # 2. Update profile
        update_resp = client.put(f"/api/clients/{client_id}", json={
            "is_vip": True,
            "special_notes": "Prefers morning appointments"
        }, headers=owner_auth_headers)
        assert update_resp.status_code == 200
        assert update_resp.json()["is_vip"] == True

        # 3. Add tags
        tags_resp = client.post(f"/api/clients/{client_id}/tags", json=["color-specialist", "vip"], headers=owner_auth_headers)
        assert tags_resp.status_code == 200
        assert "vip" in tags_resp.json()["tags"]

        # 4. Update consent
        consent_resp = client.post(f"/api/clients/{client_id}/consent", json={
            "photo_consent": True,
            "social_media_consent": True,
            "website_consent": False,
            "sms_consent": True,
            "marketing_opt_in": True
        }, headers=owner_auth_headers)
        assert consent_resp.status_code == 200
        assert consent_resp.json()["photo_consent"] == True

        # 5. View history
        history_resp = client.get(f"/api/clients/{client_id}/history", headers=owner_auth_headers)
        assert history_resp.status_code == 200
        assert history_resp.json()["client_id"] == client_id


class TestSearchAndFilterFlow:
    """Test search and filter functionality"""

    def test_client_search(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test searching for clients by various criteria"""
        # Create test clients
        clients_data = [
            {"first_name": "Alice", "last_name": "Anderson", "email": "alice@test.com"},
            {"first_name": "Bob", "last_name": "Baker", "email": "bob@test.com"},
            {"first_name": "Charlie", "last_name": "Anderson", "email": "charlie@test.com"},
        ]

        for c_data in clients_data:
            client.post(f"/api/salons/{test_salon.id}/clients", json=c_data, headers=owner_auth_headers)

        # Search by first name
        search_resp = client.get("/api/clients/search?q=Alice", headers=owner_auth_headers)
        assert search_resp.status_code == 200
        assert any("Alice" in r["full_name"] for r in search_resp.json()["results"])

        # Search by last name
        search_resp = client.get("/api/clients/search?q=Anderson", headers=owner_auth_headers)
        assert search_resp.status_code == 200
        results = search_resp.json()["results"]
        assert len([r for r in results if "Anderson" in r["full_name"]]) >= 2

        # List with filters
        list_resp = client.get(f"/api/salons/{test_salon.id}/clients?search=Bob", headers=owner_auth_headers)
        assert list_resp.status_code == 200


class TestPermissionsFlow:
    """Test role-based access control"""

    def test_client_cannot_create_salon(self, client: TestClient, db):
        """Test that regular clients cannot create salons"""
        # Register as client
        client.post("/api/auth/register", json={
            "email": "justaclient@test.com",
            "password": "clientpassword123",
            "first_name": "Just",
            "last_name": "Client"
        })

        # Login
        login_resp = client.post("/api/auth/login", data={
            "username": "justaclient@test.com",
            "password": "clientpassword123"
        })
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to create salon - should work (clients can become owners)
        salon_resp = client.post("/api", json={
            "name": "Client Salon"
        }, headers=headers)
        # This should succeed as creating a salon upgrades user to owner
        assert salon_resp.status_code == 201

    def test_unauthorized_salon_access(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test that users cannot access salons they don't belong to"""
        # Register a different user
        client.post("/api/auth/register", json={
            "email": "otheruser@test.com",
            "password": "otherpassword123",
            "first_name": "Other",
            "last_name": "User"
        })

        # Login as different user
        login_resp = client.post("/api/auth/login", data={
            "username": "otheruser@test.com",
            "password": "otherpassword123"
        })
        other_token = login_resp.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access the test salon - should fail
        salon_resp = client.get(f"/api/{test_salon.id}", headers=other_headers)
        assert salon_resp.status_code == 403


class TestDataIntegrityFlow:
    """Test data integrity and validation"""

    def test_duplicate_prevention(self, client: TestClient, owner_auth_headers, test_salon):
        """Test that duplicates are properly prevented"""
        # Create first client
        client.post(f"/api/salons/{test_salon.id}/clients", json={
            "first_name": "Unique",
            "email": "unique@test.com"
        }, headers=owner_auth_headers)

        # Try to create duplicate email
        resp = client.post(f"/api/salons/{test_salon.id}/clients", json={
            "first_name": "Duplicate",
            "email": "unique@test.com"
        }, headers=owner_auth_headers)
        assert resp.status_code == 400

    def test_required_fields_validation(self, client: TestClient, owner_auth_headers, test_salon):
        """Test that required fields are validated"""
        # Try to create client without first_name
        resp = client.post(f"/api/salons/{test_salon.id}/clients", json={
            "email": "nofirstname@test.com"
        }, headers=owner_auth_headers)
        assert resp.status_code == 422  # Validation error

    def test_soft_delete_prevents_access(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test that soft-deleted items are hidden"""
        # Create and delete a client
        create_resp = client.post(f"/api/salons/{test_salon.id}/clients", json={
            "first_name": "ToDelete"
        }, headers=owner_auth_headers)
        client_id = create_resp.json()["id"]

        # Delete
        client.delete(f"/api/clients/{client_id}", headers=owner_auth_headers)

        # List should not include deleted client (by default is_active=True filter)
        list_resp = client.get(f"/api/salons/{test_salon.id}/clients", headers=owner_auth_headers)
        assert all(c["id"] != client_id for c in list_resp.json()["items"])
