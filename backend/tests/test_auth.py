"""
Automated Pytest Test Suite - Authentication APIs
Tests: Registration, Login, Invalid Password, Invalid JWT Token
"""

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app

TEST_EMAIL = f"qa_test_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "StrongTestPassword123!"
TEST_NAME = "QA Automated Tester"


@pytest.mark.anyio
async def test_register_user_success():
    """Test user registration endpoint with valid data."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": TEST_NAME
        })
    assert response.status_code in [200, 201]


@pytest.mark.anyio
async def test_login_success():
    """Test login with valid credentials and receive JWT token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_invalid_password():
    """Test login with wrong password (should return 400/401)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/login", json={
            "email": TEST_EMAIL,
            "password": "WrongPassword999!"
        })
    assert response.status_code in [400, 401]


@pytest.mark.anyio
async def test_access_protected_route_invalid_token():
    """Test accessing protected route with invalid/fake JWT token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/auth/me", headers={
            "Authorization": "Bearer invalid_fake_jwt_token_123"
        })
    assert response.status_code in [401, 403]
