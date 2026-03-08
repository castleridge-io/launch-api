"""
Tests for API endpoints
"""

import pytest
from httpx import AsyncClient
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


class TestHealthEndpoint:
    """Tests for /health endpoint"""

    def test_health_returns_healthy(self, client):
        """Test that health endpoint returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_health_no_auth_required(self, client):
        """Test that health endpoint doesn't require authentication"""
        response = client.get("/health")
        assert response.status_code == 200


class TestRootEndpoint:
    """Tests for / endpoint"""

    def test_root_returns_service_info(self, client):
        """Test that root endpoint returns service information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Launch API"
        assert data["version"] == "1.0.0"

    def test_root_returns_platform_lists(self, client):
        """Test that root endpoint returns platform lists"""
        response = client.get("/")
        data = response.json()
        assert "platforms" in data
        assert "late_dev" in data["platforms"]
        assert "direct" in data["platforms"]
        assert "twitter" in data["platforms"]["late_dev"]
        assert "reddit" in data["platforms"]["direct"]


class TestPostEndpoint:
    """Tests for /post endpoint"""

    def test_post_requires_authentication(self, client):
        """Test that post endpoint requires authentication"""
        response = client.post(
            "/post", json={"text": "Test message", "platforms": ["twitter"]}
        )
        assert response.status_code == 401

    def test_post_with_invalid_api_key(self, client):
        """Test that post endpoint rejects invalid API key"""
        response = client.post(
            "/post",
            json={"text": "Test", "platforms": ["twitter"]},
            headers={"Authorization": "Bearer invalid_key"},
        )
        assert response.status_code == 403

    def test_post_to_late_platforms(self, client, auth_headers, mocker):
        """Test posting to Late.dev platforms"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "id": "post123",
            "url": "https://twitter.com/post/123",
        }
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={"text": "Test message", "platforms": ["twitter"], "mediaUrls": []},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform"] == "twitter"
        assert data[0]["success"] is True

    def test_post_to_reddit_success(self, client, auth_headers, mocker):
        """Test successful Reddit posting"""
        mock_submission = mocker.Mock()
        mock_submission.id = "abc123"
        mock_submission.permalink = "/r/test/comments/abc123"

        mock_reddit = mocker.Mock()
        mock_subreddit = mocker.Mock()
        mock_subreddit.submit.return_value = mock_submission
        mock_reddit.subreddit.return_value = mock_subreddit

        mocker.patch("praw.Reddit", return_value=mock_reddit)

        response = client.post(
            "/post",
            json={
                "text": "Test message",
                "platforms": ["reddit"],
                "subreddit": "test",
                "title": "Test Title",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform"] == "reddit"
        assert data[0]["success"] is True

    def test_post_to_reddit_missing_fields(self, client, auth_headers):
        """Test Reddit posting with missing required fields"""
        response = client.post(
            "/post",
            json={"text": "Test message", "platforms": ["reddit"]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform"] == "reddit"
        assert data[0]["success"] is False
        assert "requires" in data[0]["error"].lower()

    def test_post_to_telegram_success(self, client, auth_headers, mocker):
        """Test successful Telegram posting"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"message_id": 12345}}
        mocker.patch("requests.post", return_value=mock_response)
        mocker.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"})

        response = client.post(
            "/post",
            json={
                "text": "Test message",
                "platforms": ["telegram"],
                "channel_id": "@testchannel",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform"] == "telegram"
        assert data[0]["success"] is True

    def test_post_to_telegram_missing_channel(self, client, auth_headers):
        """Test Telegram posting with missing channel_id"""
        response = client.post(
            "/post",
            json={"text": "Test message", "platforms": ["telegram"]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform"] == "telegram"
        assert data[0]["success"] is False

    def test_post_to_discord_success(self, client, auth_headers, mocker):
        """Test successful Discord posting"""
        mock_response = mocker.Mock()
        mock_response.status_code = 204
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={
                "text": "Test message",
                "platforms": ["discord"],
                "webhooks": ["https://discord.com/api/webhooks/123/abc"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform"] == "discord"
        assert data[0]["success"] is True

    def test_post_to_slack_success(self, client, auth_headers, mocker):
        """Test successful Slack posting"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={
                "text": "Test message",
                "platforms": ["slack"],
                "webhooks": ["https://hooks.slack.com/services/T00/B00/XXX"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform"] == "slack"
        assert data[0]["success"] is True

    def test_post_to_multiple_platforms(self, client, auth_headers, mocker):
        """Test posting to multiple platforms at once"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "id": "123"}
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/post",
            json={
                "text": "Test message",
                "platforms": ["twitter", "linkedin"],
                "mediaUrls": [],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        platforms = [item["platform"] for item in data]
        assert "twitter" in platforms
        assert "linkedin" in platforms
