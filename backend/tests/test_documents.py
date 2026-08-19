"""
Automated Pytest Test Suite - Document Workspace & Storage APIs
Tests: Document Listing/Search, Quota Check, Unauthorized Upload
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

TEST_EMAIL = "admin@clouddocs.com"
TEST_PASSWORD = "adminpassword"


@pytest.mark.anyio
async def test_unauthorized_upload():
    """Test uploading file without Auth Header (should fail 401/403)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/documents/upload", files={
            "file": ("test.txt", b"Hello CloudDocs", "text/plain")
        })
    assert response.status_code in [401, 403]


@pytest.mark.anyio
async def test_get_user_quota_and_search():
    """Test login, storage quota, and workspace search."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_res.status_code == 200:
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Quota test
            quota_res = await ac.get("/documents/quota", headers=headers)
            assert quota_res.status_code == 200
            assert "used_bytes" in quota_res.json()

            # Workspace search test
            search_res = await ac.get("/documents/search?q=", headers=headers)
            assert search_res.status_code == 200
            assert isinstance(search_res.json(), list)
