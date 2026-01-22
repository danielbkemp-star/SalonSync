"""
Authentication Tests for SalonSync
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthRegistration:
    """Test user registration"""

    def test_register_success(self, client: TestClient):
        """Test successful user registration"""
        response = client.post("/api/auth/register", json={
            "email": "newuser@test.com",
            "password": "securepassword123",
            "first_name": "New"
        })
        assert response.status_code == 201, f"Registration failed: {response.json()}"
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["first_name"] == "New"
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client: TestClient):
        """Test registration with existing email fails"""
        # First registration
        client.post("/api/auth/register", json={
            "email": "duplicate@test.com",
            "password": "password123abc",
            "first_name": "First"
        })
        # Second registration with same email
        response = client.post("/api/auth/register", json={
            "email": "duplicate@test.com",
            "password": "password456def",
            "first_name": "Second"
        })
        assert response.status_code == 400, "Should reject duplicate email"

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password fails"""
        response = client.post("/api/auth/register", json={
            "email": "weakpw@test.com",
            "password": "123",  # Too short
            "first_name": "Weak"
        })
        assert response.status_code == 422, "Should reject weak password"

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email fails"""
        response = client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "validpassword123",
            "first_name": "Invalid"
        })
        assert response.status_code == 422, "Should reject invalid email"


class TestAuthLogin:
    """Test user login"""

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login"""
        response = client.post("/api/auth/login", data={
            "username": "testuser@salonsync.com",
            "password": "testpassword123"
        })
        assert response.status_code == 200, f"Login failed: {response.json()}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password fails"""
        response = client.post("/api/auth/login", data={
            "username": "testuser@salonsync.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, "Should reject wrong password"

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user fails"""
        response = client.post("/api/auth/login", data={
            "username": "nobody@test.com",
            "password": "anypassword"
        })
        assert response.status_code == 401, "Should reject non-existent user"

    def test_login_case_insensitive_email(self, client: TestClient, test_user):
        """Test login works with different email casing"""
        response = client.post("/api/auth/login", data={
            "username": "TESTUSER@salonsync.com",
            "password": "testpassword123"
        })
        assert response.status_code == 200, "Should accept uppercase email"


class TestAuthMe:
    """Test current user endpoint"""

    def test_get_current_user(self, client: TestClient, auth_headers, test_user):
        """Test getting current user info"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    def test_protected_route_without_token(self, client: TestClient):
        """Test protected route without auth token fails"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401, "Should require authentication"

    def test_protected_route_invalid_token(self, client: TestClient):
        """Test protected route with invalid token fails"""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid-token"
        })
        assert response.status_code == 401, "Should reject invalid token"


class TestPasswordChange:
    """Test password change functionality"""

    def test_change_password_success(self, client: TestClient, auth_headers, test_user):
        """Test successful password change"""
        response = client.post("/api/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "testpassword123",
                "new_password": "newpassword456"
            }
        )
        assert response.status_code == 200

        # Verify can login with new password
        login_response = client.post("/api/auth/login", data={
            "username": test_user.email,
            "password": "newpassword456"
        })
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, client: TestClient, auth_headers):
        """Test password change with wrong current password fails"""
        response = client.post("/api/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword456"
            }
        )
        assert response.status_code == 400
