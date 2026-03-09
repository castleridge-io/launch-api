"""
Tests for authentication
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app, verify_api_key, API_KEY


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


class TestAuthentication:
    """Tests for API authentication"""

    def test_verify_api_key_missing_header(self):
        """Test that missing authorization header raises 401"""
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(authorization=None)

        assert exc_info.value.status_code == 401
        assert "missing" in exc_info.value.detail.lower()

    def test_verify_api_key_invalid_key(self):
        """Test that invalid API key raises 403"""
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(authorization="Bearer invalid_key")

        assert exc_info.value.status_code == 403
        assert "invalid" in exc_info.value.detail.lower()

    def test_verify_api_key_valid_key(self):
        """Test that valid API key returns True"""
        result = verify_api_key(authorization=f"Bearer {API_KEY}")
        assert result is True

    def test_verify_api_key_without_bearer_prefix(self):
        """Test API key without Bearer prefix"""
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(authorization="invalid_key")

        assert exc_info.value.status_code == 403

    def test_verify_api_key_empty_string(self):
        """Test empty authorization header"""
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(authorization="")

        assert exc_info.value.status_code == 401

    def test_verify_api_key_bearer_only(self):
        """Test 'Bearer ' without actual key"""
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(authorization="Bearer ")

        assert exc_info.value.status_code == 403

    def test_endpoint_without_auth_returns_401(self, client):
        """Test that protected endpoints return 401 without auth"""
        response = client.post("/post", json={"text": "Test", "platforms": ["twitter"]})
        assert response.status_code == 401

    def test_endpoint_with_wrong_auth_returns_403(self, client):
        """Test that protected endpoints return 403 with wrong auth"""
        response = client.post(
            "/post",
            json={"text": "Test", "platforms": ["twitter"]},
            headers={"Authorization": "Bearer wrong_key"},
        )
        assert response.status_code == 403

    def test_endpoint_with_correct_auth_succeeds(self, client, mocker):
        """Test that protected endpoints succeed with correct auth"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "id": "123"}
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={"text": "Test", "platforms": ["twitter"], "mediaUrls": []},
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        assert response.status_code == 200

    def test_platform_endpoint_requires_auth(self, client):
        """Test that platform-specific endpoints require authentication"""
        endpoints = [
            ("/reddit?subreddit=test&title=Test&text=Test", "post"),
            ("/telegram?channel_id=@test&text=Test", "post"),
            ("/discord?webhook_url=http://test.com&text=Test", "post"),
            ("/slack?webhook_url=http://test.com&text=Test", "post"),
        ]

        for endpoint, method in endpoints:
            if method == "post":
                response = client.post(endpoint)
            else:
                response = client.get(endpoint)

            assert response.status_code == 401, (
                f"Endpoint {endpoint} should require auth"
            )
