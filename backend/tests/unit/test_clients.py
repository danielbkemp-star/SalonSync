"""
Client CRUD Tests for SalonSync
"""
import pytest
from fastapi.testclient import TestClient


class TestClientCreate:
    """Test client creation"""

    def test_create_client_success(self, client: TestClient, owner_auth_headers, test_salon):
        """Test successful client creation"""
        response = client.post(f"/api/salons/{test_salon.id}/clients", json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@test.com",
            "phone": "555-123-4567"
        }, headers=owner_auth_headers)
        assert response.status_code == 201, f"Create failed: {response.json()}"
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Doe"
        assert data["email"] == "jane@test.com"

    def test_create_client_minimal(self, client: TestClient, owner_auth_headers, test_salon):
        """Test client creation with minimal fields"""
        response = client.post(f"/api/salons/{test_salon.id}/clients", json={
            "first_name": "John"
        }, headers=owner_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["id"] is not None  # Auto-generated ID

    def test_create_client_duplicate_email(self, client: TestClient, owner_auth_headers, test_salon):
        """Test client creation with duplicate email fails"""
        # Create first client
        client.post(f"/api/salons/{test_salon.id}/clients", json={
            "first_name": "First",
            "email": "duplicate@test.com"
        }, headers=owner_auth_headers)

        # Try to create another with same email
        response = client.post(f"/api/salons/{test_salon.id}/clients", json={
            "first_name": "Second",
            "email": "duplicate@test.com"
        }, headers=owner_auth_headers)
        assert response.status_code == 400

    def test_create_client_with_hair_profile(self, client: TestClient, owner_auth_headers, test_salon):
        """Test client creation with hair profile"""
        response = client.post(f"/api/salons/{test_salon.id}/clients", json={
            "first_name": "Hair",
            "last_name": "Client",
            "hair_profile": {
                "hair_type": "fine",
                "hair_color": "brunette",
                "hair_texture": "wavy",
                "hair_length": "medium"
            }
        }, headers=owner_auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["hair_type"] == "fine"
        assert data["hair_texture"] == "wavy"


class TestClientRead:
    """Test client retrieval"""

    def test_list_clients(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test listing clients"""
        # Create test clients
        from app.models import Client
        for i in range(3):
            c = Client(
                salon_id=test_salon.id,
                first_name=f"Client{i}",
                last_name=f"Test{i}"
            )
            db.add(c)
        db.commit()

        response = client.get(f"/api/salons/{test_salon.id}/clients", headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3

    def test_get_client_by_id(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test getting client by ID"""
        from app.models import Client
        test_client = Client(
            salon_id=test_salon.id,
            first_name="Get",
            last_name="Test"
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        response = client.get(f"/api/clients/{test_client.id}", headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Get"

    def test_get_nonexistent_client(self, client: TestClient, owner_auth_headers):
        """Test getting non-existent client returns 404"""
        response = client.get("/api/clients/99999", headers=owner_auth_headers)
        assert response.status_code == 404

    def test_search_clients(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test searching clients"""
        from app.models import Client
        test_client = Client(
            salon_id=test_salon.id,
            first_name="Searchable",
            last_name="Person",
            email="search@test.com"
        )
        db.add(test_client)
        db.commit()

        response = client.get(f"/api/clients/search?q=Searchable", headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert any(c["full_name"] == "Searchable Person" for c in data["results"])


class TestClientUpdate:
    """Test client updates"""

    def test_update_client_success(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test successful client update"""
        from app.models import Client
        test_client = Client(
            salon_id=test_salon.id,
            first_name="Original",
            last_name="Name"
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        response = client.put(f"/api/clients/{test_client.id}", json={
            "first_name": "Updated",
            "is_vip": True
        }, headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["is_vip"] == True


class TestClientConsent:
    """Test client consent management"""

    def test_update_consent(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test updating client consent"""
        from app.models import Client
        test_client = Client(
            salon_id=test_salon.id,
            first_name="Consent",
            last_name="Test"
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        response = client.post(f"/api/clients/{test_client.id}/consent", json={
            "photo_consent": True,
            "social_media_consent": True,
            "website_consent": False,
            "sms_consent": True,
            "marketing_opt_in": False
        }, headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["photo_consent"] == True
        assert data["social_media_consent"] == True
        assert data["marketing_opt_in"] == False

    def test_get_consent(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test getting client consent status"""
        from app.models import Client
        test_client = Client(
            salon_id=test_salon.id,
            first_name="Consent",
            last_name="Check",
            photo_consent=True,
            social_media_consent=False
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        response = client.get(f"/api/clients/{test_client.id}/consent", headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["photo_consent"] == True
        assert data["social_media_consent"] == False


class TestClientTags:
    """Test client tagging"""

    def test_add_tags(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test adding tags to client"""
        from app.models import Client
        test_client = Client(
            salon_id=test_salon.id,
            first_name="Tag",
            last_name="Test"
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        response = client.post(f"/api/clients/{test_client.id}/tags", json=["vip", "color-client"], headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "vip" in data["tags"]
        assert "color-client" in data["tags"]

    def test_remove_tag(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test removing tag from client"""
        from app.models import Client
        test_client = Client(
            salon_id=test_salon.id,
            first_name="Tag",
            last_name="Remove",
            tags=["vip", "remove-me"]
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        response = client.delete(f"/api/clients/{test_client.id}/tags/remove-me", headers=owner_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "remove-me" not in data["tags"]
        assert "vip" in data["tags"]


class TestClientDelete:
    """Test client deletion"""

    def test_delete_client(self, client: TestClient, owner_auth_headers, test_salon, db):
        """Test client soft delete"""
        from app.models import Client
        test_client = Client(
            salon_id=test_salon.id,
            first_name="Delete",
            last_name="Me"
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        response = client.delete(f"/api/clients/{test_client.id}", headers=owner_auth_headers)
        assert response.status_code == 200

        # Verify soft delete
        db.refresh(test_client)
        assert test_client.is_active == False
