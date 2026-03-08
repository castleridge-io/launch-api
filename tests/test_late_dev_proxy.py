"""
Tests for Late.dev proxy functionality
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import post_via_late, LATE_PLATFORMS


class TestLateDevProxy:
    """Tests for Late.dev proxy integration"""

    @pytest.mark.asyncio
    async def test_post_via_late_no_api_key(self, mocker):
        """Test Late.dev posting without API key configured"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": ""}, clear=True)

        result = await post_via_late(
            text="Test message", platforms=["twitter"], media_urls=[]
        )

        assert result["success"] is False
        assert "not configured" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_via_late_no_supported_platforms(self, mocker):
        """Test Late.dev with non-supported platforms"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        result = await post_via_late(
            text="Test message", platforms=["reddit", "telegram"], media_urls=[]
        )

        assert result["success"] is False
        assert "no late-supported platforms" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_via_late_success(self, mocker):
        """Test successful Late.dev posting"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "id": "post123",
            "url": "https://twitter.com/post/123",
        }
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        result = await post_via_late(
            text="Test message",
            platforms=["twitter", "linkedin"],
            media_urls=["https://example.com/image.jpg"],
        )

        assert result["success"] is True
        assert result["id"] == "post123"

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "https://getlate.dev/api/v1/posts" in call_args[0]
        assert call_args[1]["json"]["text"] == "Test message"
        assert "twitter" in call_args[1]["json"]["platforms"]
        assert "linkedin" in call_args[1]["json"]["platforms"]

    @pytest.mark.asyncio
    async def test_post_via_late_api_error(self, mocker):
        """Test Late.dev API error handling"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        mock_response = mocker.Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request: Invalid platform"
        mocker.patch("requests.post", return_value=mock_response)

        result = await post_via_late(
            text="Test message", platforms=["twitter"], media_urls=[]
        )

        assert result["success"] is False
        assert "late api error" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_via_late_network_error(self, mocker):
        """Test Late.dev network error handling"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        mocker.patch("requests.post", side_effect=Exception("Network error"))

        result = await post_via_late(
            text="Test message", platforms=["twitter"], media_urls=[]
        )

        assert result["success"] is False
        assert "network error" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_via_late_timeout(self, mocker):
        """Test Late.dev timeout handling"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        import requests

        mocker.patch("requests.post", side_effect=requests.Timeout("Request timed out"))

        result = await post_via_late(
            text="Test message", platforms=["twitter"], media_urls=[]
        )

        assert result["success"] is False
        assert "timed out" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_post_via_late_with_media(self, mocker):
        """Test Late.dev posting with media URLs"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "id": "123"}
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        media_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
        ]

        result = await post_via_late(
            text="Test with media", platforms=["instagram"], media_urls=media_urls
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert call_args[1]["json"]["mediaUrls"] == media_urls

    @pytest.mark.asyncio
    async def test_post_via_late_filters_platforms(self, mocker):
        """Test that only Late-supported platforms are sent"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "id": "123"}
        mock_post = mocker.patch("requests.post", return_value=mock_response)

        result = await post_via_late(
            text="Test message",
            platforms=["twitter", "reddit", "linkedin", "telegram"],
            media_urls=[],
        )

        call_args = mock_post.call_args
        sent_platforms = call_args[1]["json"]["platforms"]
        assert "twitter" in sent_platforms
        assert "linkedin" in sent_platforms
        assert "reddit" not in sent_platforms
        assert "telegram" not in sent_platforms

    def test_late_platforms_list(self):
        """Test that LATE_PLATFORMS contains expected platforms"""
        expected_platforms = [
            "twitter",
            "linkedin",
            "facebook",
            "instagram",
            "tiktok",
            "youtube",
            "pinterest",
            "threads",
            "bluesky",
        ]

        for platform in expected_platforms:
            assert platform in LATE_PLATFORMS, f"{platform} should be in LATE_PLATFORMS"

    @pytest.mark.asyncio
    async def test_post_via_late_201_response(self, mocker):
        """Test Late.dev with 201 Created response"""
        mocker.patch.dict(os.environ, {"LATE_API_KEY": "test_key"})

        mock_response = mocker.Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "id": "post456",
            "url": "https://linkedin.com/post/456",
        }
        mocker.patch("requests.post", return_value=mock_response)

        result = await post_via_late(
            text="Test message", platforms=["linkedin"], media_urls=[]
        )

        assert result["success"] is True
        assert result["id"] == "post456"
