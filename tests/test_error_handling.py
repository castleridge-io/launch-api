"""
Tests for error handling
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app, API_KEY


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create auth headers with valid API key"""
    return {"Authorization": f"Bearer {API_KEY}"}


class TestErrorHandling:
    """Tests for error handling across the API"""

    def test_invalid_json_returns_422(self, client, auth_headers):
        """Test that invalid JSON returns 422 error"""
        response = client.post(
            "/post",
            content="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client, auth_headers):
        """Test that missing required fields returns 422"""
        response = client.post(
            "/post", json={"platforms": ["twitter"]}, headers=auth_headers
        )
        assert response.status_code == 422

    def test_empty_platforms_list(self, client, auth_headers):
        """Test posting with empty platforms list"""
        response = client.post(
            "/post", json={"text": "Test", "platforms": []}, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_invalid_platform_name(self, client, auth_headers, mocker):
        """Test posting with invalid platform name"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={
                "text": "Test",
                "platforms": ["invalid_platform", "twitter"],
                "mediaUrls": [],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform"] == "twitter"

    def test_late_api_rate_limit(self, client, auth_headers, mocker):
        """Test handling Late API rate limiting"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        mock_response = mocker.Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={"text": "Test", "platforms": ["twitter"], "mediaUrls": []},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data[0]["success"] is False
        assert "rate limit" in data[0]["error"].lower()

    def test_late_api_server_error(self, client, auth_headers, mocker):
        """Test handling Late API server errors"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        mock_response = mocker.Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={"text": "Test", "platforms": ["twitter"], "mediaUrls": []},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data[0]["success"] is False
        assert "late api error" in data[0]["error"].lower()

    def test_network_timeout_handling(self, client, auth_headers, mocker):
        """Test handling network timeouts"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        import requests

        mocker.patch("requests.post", side_effect=requests.Timeout())

        response = client.post(
            "/post",
            json={"text": "Test", "platforms": ["twitter"], "mediaUrls": []},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data[0]["success"] is False

    def test_connection_error_handling(self, client, auth_headers, mocker):
        """Test handling connection errors"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        import requests

        mocker.patch("requests.post", side_effect=requests.ConnectionError())

        response = client.post(
            "/post",
            json={"text": "Test", "platforms": ["twitter"], "mediaUrls": []},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data[0]["success"] is False

    def test_malformed_response_handling(self, client, auth_headers, mocker):
        """Test handling malformed API responses"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={"text": "Test", "platforms": ["twitter"], "mediaUrls": []},
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_partial_platform_failure(self, client, auth_headers, mocker):
        """Test handling when some platforms succeed and some fail"""
        mocker.patch.dict(
            os.environ, {"LATE_API_KEY": "test_key", "TELEGRAM_BOT_TOKEN": "test_token"}
        )

        late_response = mocker.Mock()
        late_response.status_code = 200
        late_response.json.return_value = {"success": True, "id": "123"}

        telegram_response = mocker.Mock()
        telegram_response.status_code = 400
        telegram_response.text = "Bad Request"

        def mock_post(url, **kwargs):
            if "getlate.dev" in url:
                return late_response
            else:
                return telegram_response

        mocker.patch("requests.post", side_effect=mock_post)

        response = client.post(
            "/post",
            json={
                "text": "Test",
                "platforms": ["twitter", "telegram"],
                "channel_id": "@test",
                "mediaUrls": [],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        twitter_result = next((r for r in data if r["platform"] == "twitter"), None)
        telegram_result = next((r for r in data if r["platform"] == "telegram"), None)

        assert twitter_result["success"] is True
        assert telegram_result["success"] is False

    def test_empty_text_field(self, client, auth_headers):
        """Test posting with empty text field"""
        response = client.post(
            "/post", json={"text": "", "platforms": ["twitter"]}, headers=auth_headers
        )
        assert response.status_code == 200

    def test_very_long_text(self, client, auth_headers, mocker):
        """Test posting with very long text"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "id": "123"}
        mocker.patch("requests.post", return_value=mock_response)

        long_text = "A" * 10000

        response = client.post(
            "/post",
            json={"text": long_text, "platforms": ["twitter"], "mediaUrls": []},
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_special_characters_in_text(self, client, auth_headers, mocker):
        """Test posting with special characters"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "id": "123"}
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        special_text = "Test with émojis 🚀 and spëcial çhars <>&\"'"

        response = client.post(
            "/post",
            json={"text": special_text, "platforms": ["twitter"], "mediaUrls": []},
            headers=auth_headers,
        )

        assert response.status_code == 200
        call_args = mock_post.call_args
        assert call_args[1]["json"]["text"] == special_text

    def test_unicode_handling(self, client, auth_headers, mocker):
        """Test handling unicode characters"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "id": "123"}
        mocker.patch("requests.post", return_value=mock_response)

        unicode_text = "测试中文 日本語 العربية עברית"

        response = client.post(
            "/post",
            json={"text": unicode_text, "platforms": ["twitter"], "mediaUrls": []},
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_null_values_in_optional_fields(self, client, auth_headers, mocker):
        """Test handling null values in optional fields"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "id": "123"}
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={
                "text": "Test",
                "platforms": ["twitter"],
                "mediaUrls": None,
                "subreddit": None,
                "title": None,
                "channel_id": None,
                "webhooks": None,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_invalid_media_urls(self, client, auth_headers, mocker):
        """Test handling invalid media URLs"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "id": "123"}
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={
                "text": "Test",
                "platforms": ["twitter"],
                "mediaUrls": ["not-a-url", "also-not-url"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_multiple_webhooks(self, client, auth_headers, mocker):
        """Test posting to multiple webhooks"""
        mock_response = mocker.Mock()
        mock_response.status_code = 204
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={
                "text": "Test",
                "platforms": ["discord"],
                "webhooks": [
                    "https://discord.com/api/webhooks/1/a",
                    "https://discord.com/api/webhooks/2/b",
                    "https://discord.com/api/webhooks/3/c",
                ],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for result in data:
            assert result["platform"] == "discord"
            assert result["success"] is True
