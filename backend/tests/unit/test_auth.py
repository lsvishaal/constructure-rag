"""
Authentication unit tests.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import pytest

from src.core.config import PROJECT_CONTEXT_ID, BUILD_WATERMARK, settings
from src.services.auth import AuthService, get_auth_service
from src.models.auth import UserCreate


class TestAuthService:
    """Test suite for AuthService."""
    
    def test_auth_service_has_watermark(self, auth_service):
        """Auth service should have watermark."""
        assert auth_service.watermark == BUILD_WATERMARK
        assert auth_service.project_id == PROJECT_CONTEXT_ID
    
    def test_password_hashing(self, auth_service):
        """Password hashing should work correctly."""
        password = "test_password_123"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert auth_service.verify_password(password, hashed)
        assert not auth_service.verify_password("wrong_password", hashed)
    
    def test_test_user_initialized(self, auth_service):
        """Test user should be initialized on startup."""
        user = auth_service.get_user(settings.test_user_email)
        
        assert user is not None
        assert user.email == settings.test_user_email
        assert user.watermark == BUILD_WATERMARK
    
    def test_authenticate_valid_user(self, auth_service):
        """Valid credentials should authenticate successfully."""
        user = auth_service.authenticate_user(
            settings.test_user_email,
            settings.test_user_password
        )
        
        assert user is not None
        assert user.email == settings.test_user_email
    
    def test_authenticate_invalid_password(self, auth_service):
        """Invalid password should fail authentication."""
        user = auth_service.authenticate_user(
            settings.test_user_email,
            "wrong_password"
        )
        
        assert user is None
    
    def test_authenticate_nonexistent_user(self, auth_service):
        """Non-existent user should fail authentication."""
        user = auth_service.authenticate_user(
            "nonexistent@example.com",
            "any_password"
        )
        
        assert user is None
    
    def test_create_access_token(self, auth_service):
        """Access token should be created with watermark."""
        token = auth_service.create_access_token(data={"sub": "test@example.com"})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_valid_token(self, auth_service):
        """Valid token should decode correctly."""
        email = "test@example.com"
        token = auth_service.create_access_token(data={"sub": email})
        
        token_data = auth_service.decode_token(token)
        
        assert token_data.email == email
    
    def test_login_returns_token(self, auth_service):
        """Login should return access token."""
        token = auth_service.login(
            settings.test_user_email,
            settings.test_user_password
        )
        
        assert token is not None
        assert token.access_token is not None
        assert token.token_type == "bearer"
        assert token.watermark == BUILD_WATERMARK


class TestAuthAPI:
    """Test suite for Auth API endpoints."""
    
    def test_health_check(self, client):
        """Health check should return watermark headers."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        assert response.headers.get("X-Project-Id") == PROJECT_CONTEXT_ID
        assert response.headers.get("X-Build-Watermark") == BUILD_WATERMARK
    
    def test_login_with_valid_credentials(self, client, test_user_credentials):
        """Login with valid credentials should succeed."""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": test_user_credentials["email"],
                "password": test_user_credentials["password"],
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["watermark"] == BUILD_WATERMARK
    
    def test_login_with_invalid_credentials(self, client):
        """Login with invalid credentials should fail."""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "wrong@example.com",
                "password": "wrong_password",
            }
        )
        
        assert response.status_code == 401
    
    def test_get_current_user(self, client, auth_headers):
        """Get current user should return user data."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == settings.test_user_email
        assert data["project_context"] == PROJECT_CONTEXT_ID
    
    def test_get_current_user_without_token(self, client):
        """Get current user without token should fail."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_verify_token(self, client, auth_headers):
        """Verify token should return valid status."""
        response = client.get("/api/v1/auth/verify", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["watermark"] == BUILD_WATERMARK
