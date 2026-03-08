"""
Tests for platform adapters (Reddit, Telegram, Discord, Slack)
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import post_to_reddit, post_to_telegram, post_to_discord, post_to_slack


class TestRedditAdapter:
    """Tests for Reddit posting adapter"""

    @pytest.mark.asyncio
    async def test_post_to_reddit_success(self, mocker):
        """Test successful Reddit post"""
        mock_submission = mocker.Mock()
        mock_submission.id = "abc123"
        mock_submission.permalink = "/r/test/comments/abc123"

        mock_subreddit = mocker.Mock()
        mock_subreddit.submit.return_value = mock_submission

        mock_reddit = mocker.Mock()
        mock_reddit.subreddit.return_value = mock_subreddit

        mocker.patch("praw.Reddit", return_value=mock_reddit)

        result = await post_to_reddit(
            subreddit="test", title="Test Title", text="Test content"
        )

        assert result["success"] is True
        assert result["platform"] == "reddit"
        assert result["post_id"] == "abc123"
        assert "reddit.com" in result["url"]

    @pytest.mark.asyncio
    async def test_post_to_reddit_praw_not_installed(self, mocker):
        """Test Reddit posting when PRAW is not installed"""
        mocker.patch.dict(sys.modules, {"praw": None})

        result = await post_to_reddit(
            subreddit="test", title="Test Title", text="Test content"
        )

        assert result["success"] is False
        assert result["platform"] == "reddit"
        assert "praw not installed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_to_reddit_auth_error(self, mocker):
        """Test Reddit posting with authentication error"""
        mock_reddit = mocker.Mock()
        mock_reddit.subreddit.side_effect = Exception("Invalid credentials")
        mocker.patch("praw.Reddit", return_value=mock_reddit)

        result = await post_to_reddit(
            subreddit="test", title="Test Title", text="Test content"
        )

        assert result["success"] is False
        assert result["platform"] == "reddit"
        assert "invalid credentials" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_to_reddit_subreddit_error(self, mocker):
        """Test Reddit posting with subreddit error"""
        mock_reddit = mocker.Mock()
        mock_reddit.subreddit.side_effect = Exception("Subreddit not found")
        mocker.patch("praw.Reddit", return_value=mock_reddit)

        result = await post_to_reddit(
            subreddit="nonexistent", title="Test Title", text="Test content"
        )

        assert result["success"] is False
        assert "subreddit not found" in result["error"].lower()


class TestTelegramAdapter:
    """Tests for Telegram posting adapter"""

    @pytest.mark.asyncio
    async def test_post_to_telegram_success(self, mocker):
        """Test successful Telegram post"""
        mocker.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"})

        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"message_id": 12345}}
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        result = await post_to_telegram(channel_id="@testchannel", text="Test message")

        assert result["success"] is True
        assert result["platform"] == "telegram"
        assert result["post_id"] == "12345"
        assert "t.me" in result["url"]

    @pytest.mark.asyncio
    async def test_post_to_telegram_no_token(self, mocker):
        """Test Telegram posting without bot token"""
        mocker.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}, clear=True)

        result = await post_to_telegram(channel_id="@testchannel", text="Test message")

        assert result["success"] is False
        assert "token not configured" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_to_telegram_api_error(self, mocker):
        """Test Telegram API error"""
        mocker.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"})

        mock_response = mocker.Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request: Chat not found"
        mocker.patch("requests.post", return_value=mock_response)

        result = await post_to_telegram(channel_id="@nonexistent", text="Test message")

        assert result["success"] is False
        assert result["platform"] == "telegram"
        assert "chat not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_to_telegram_network_error(self, mocker):
        """Test Telegram network error"""
        mocker.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"})

        mocker.patch("requests.post", side_effect=Exception("Network error"))

        result = await post_to_telegram(channel_id="@testchannel", text="Test message")

        assert result["success"] is False
        assert result["platform"] == "telegram"
        assert "network error" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_to_telegram_with_markdown(self, mocker):
        """Test Telegram post with markdown parsing"""
        mocker.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"})

        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"message_id": 12345}}
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        result = await post_to_telegram(
            channel_id="@testchannel", text="**Bold** _italic_ text"
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert call_args[1]["json"]["parse_mode"] == "Markdown"


class TestDiscordAdapter:
    """Tests for Discord webhook adapter"""

    @pytest.mark.asyncio
    async def test_post_to_discord_success(self, mocker):
        """Test successful Discord post"""
        mock_response = mocker.Mock()
        mock_response.status_code = 204
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        result = await post_to_discord(
            webhook_url="https://discord.com/api/webhooks/123/abc", text="Test message"
        )

        assert result["success"] is True
        assert result["platform"] == "discord"

        call_args = mock_post.call_args
        assert call_args[1]["json"]["content"] == "Test message"
        assert call_args[1]["json"]["username"] == "Launch Bot"

    @pytest.mark.asyncio
    async def test_post_to_discord_error(self, mocker):
        """Test Discord webhook error"""
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_response.text = "Unknown Webhook"
        mocker.patch("requests.post", return_value=mock_response)

        result = await post_to_discord(
            webhook_url="https://discord.com/api/webhooks/invalid", text="Test message"
        )

        assert result["success"] is False
        assert result["platform"] == "discord"
        assert "unknown webhook" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_to_discord_network_error(self, mocker):
        """Test Discord network error"""
        mocker.patch("requests.post", side_effect=Exception("Connection failed"))

        result = await post_to_discord(
            webhook_url="https://discord.com/api/webhooks/123/abc", text="Test message"
        )

        assert result["success"] is False
        assert result["platform"] == "discord"
        assert "connection failed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_to_discord_timeout(self, mocker):
        """Test Discord timeout"""
        import requests

        mocker.patch("requests.post", side_effect=requests.Timeout())

        result = await post_to_discord(
            webhook_url="https://discord.com/api/webhooks/123/abc", text="Test message"
        )

        assert result["success"] is False


class TestSlackAdapter:
    """Tests for Slack webhook adapter"""

    @pytest.mark.asyncio
    async def test_post_to_slack_success(self, mocker):
        """Test successful Slack post"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        result = await post_to_slack(
            webhook_url="https://hooks.slack.com/services/T00/B00/XXX",
            text="Test message",
        )

        assert result["success"] is True
        assert result["platform"] == "slack"

        call_args = mock_post.call_args
        assert call_args[1]["json"]["text"] == "Test message"
        assert call_args[1]["json"]["username"] == "Launch Bot"
        assert call_args[1]["json"]["icon_emoji"] == ":rocket:"

    @pytest.mark.asyncio
    async def test_post_to_slack_error(self, mocker):
        """Test Slack webhook error"""
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        mock_response.text = "No service"
        mocker.patch("requests.post", return_value=mock_response)

        result = await post_to_slack(
            webhook_url="https://hooks.slack.com/services/invalid", text="Test message"
        )

        assert result["success"] is False
        assert result["platform"] == "slack"
        assert "no service" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_to_slack_network_error(self, mocker):
        """Test Slack network error"""
        mocker.patch("requests.post", side_effect=Exception("Network timeout"))

        result = await post_to_slack(
            webhook_url="https://hooks.slack.com/services/T00/B00/XXX",
            text="Test message",
        )

        assert result["success"] is False
        assert result["platform"] == "slack"
        assert "network timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_to_slack_timeout(self, mocker):
        """Test Slack timeout"""
        import requests

        mocker.patch("requests.post", side_effect=requests.Timeout())

        result = await post_to_slack(
            webhook_url="https://hooks.slack.com/services/T00/B00/XXX",
            text="Test message",
        )

        assert result["success"] is False


class TestPlatformSpecificEndpoints:
    """Tests for platform-specific API endpoints"""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from server import app

        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        from server import API_KEY

        return {"Authorization": f"Bearer {API_KEY}"}

    def test_reddit_endpoint_success(self, client, auth_headers, mocker):
        """Test Reddit-specific endpoint"""
        mock_submission = mocker.Mock()
        mock_submission.id = "test123"
        mock_submission.permalink = "/r/test/comments/test123"

        mock_reddit = mocker.Mock()
        mock_subreddit = mocker.Mock()
        mock_subreddit.submit.return_value = mock_submission
        mock_reddit.subreddit.return_value = mock_subreddit

        mocker.patch("praw.Reddit", return_value=mock_reddit)

        response = client.post(
            "/reddit?subreddit=test&title=Test&text=Content", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "reddit"
        assert data["success"] is True

    def test_telegram_endpoint_success(self, client, auth_headers, mocker):
        """Test Telegram-specific endpoint"""
        mocker.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token"})

        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {"message_id": 123}}
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/telegram?channel_id=@test&text=Test", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "telegram"
        assert data["success"] is True

    def test_discord_endpoint_success(self, client, auth_headers, mocker):
        """Test Discord-specific endpoint"""
        mock_response = mocker.Mock()
        mock_response.status_code = 204
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/discord?webhook_url=http://test.com&text=Test", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "discord"
        assert data["success"] is True

    def test_slack_endpoint_success(self, client, auth_headers, mocker):
        """Test Slack-specific endpoint"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mocker.patch("requests.post", return_value=mock_response)

        response = client.post(
            "/slack?webhook_url=http://test.com&text=Test", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "slack"
        assert data["success"] is True
