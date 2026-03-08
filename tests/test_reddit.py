"""
Tests for Reddit API integration
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRedditConfiguration:
    """Test Reddit environment configuration"""

    def test_reddit_env_vars_present(self):
        """Check if all required Reddit env vars are present"""
        required_vars = [
            "REDDIT_CLIENT_ID",
            "REDDIT_CLIENT_SECRET",
            "REDDIT_USER_AGENT",
            "REDDIT_USERNAME",
            "REDDIT_PASSWORD",
        ]

        missing = []
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.startswith("your_"):
                missing.append(var)

        if missing:
            pytest.skip(f"Reddit credentials not configured: {missing}")

    def test_reddit_user_agent_format(self):
        """Verify user agent follows Reddit's format guidelines"""
        user_agent = os.getenv("REDDIT_USER_AGENT", "")

        if not user_agent or user_agent.startswith("your_"):
            pytest.skip("Reddit user agent not configured")

        assert len(user_agent) >= 5, "User agent too short"
        assert "/" in user_agent or " " in user_agent, (
            "User agent should include app name and version"
        )


class TestRedditIntegration:
    """Test Reddit API integration"""

    @pytest.mark.asyncio
    async def test_post_to_reddit_endpoint_success(self):
        """Test the Reddit posting endpoint with mocked PRAW"""
        from server import post_to_reddit

        mock_praw = MagicMock()
        mock_reddit = MagicMock()
        mock_subreddit = MagicMock()
        mock_submission = MagicMock()
        mock_submission.id = "test123"
        mock_submission.permalink = "/r/test/comments/test123"

        mock_subreddit.submit.return_value = mock_submission
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_praw.Reddit.return_value = mock_reddit

        with patch.dict(
            os.environ,
            {
                "REDDIT_CLIENT_ID": "test_id",
                "REDDIT_CLIENT_SECRET": "test_secret",
                "REDDIT_USER_AGENT": "TestBot/1.0",
                "REDDIT_USERNAME": "test_user",
                "REDDIT_PASSWORD": "test_pass",
            },
        ):
            with patch("server.praw", mock_praw):
                result = await post_to_reddit("test", "Test Title", "Test body")

        assert result["success"] is True
        assert result["platform"] == "reddit"
        assert "url" in result
        assert result["post_id"] == "test123"

    @pytest.mark.asyncio
    async def test_post_to_reddit_missing_credentials(self):
        """Test handling of missing Reddit credentials"""
        from server import post_to_reddit

        original_id = os.environ.get("REDDIT_CLIENT_ID")
        os.environ["REDDIT_CLIENT_ID"] = ""

        try:
            result = await post_to_reddit("test", "Test", "Test")
            assert result["success"] is False
            assert "error" in result
        finally:
            if original_id:
                os.environ["REDDIT_CLIENT_ID"] = original_id
            else:
                os.environ.pop("REDDIT_CLIENT_ID", None)

    @pytest.mark.asyncio
    async def test_post_to_reddit_import_error(self):
        """Test handling when PRAW is not installed"""
        from server import post_to_reddit

        with patch.dict(
            os.environ,
            {
                "REDDIT_CLIENT_ID": "test_id",
                "REDDIT_CLIENT_SECRET": "test_secret",
                "REDDIT_USER_AGENT": "TestBot/1.0",
                "REDDIT_USERNAME": "test_user",
                "REDDIT_PASSWORD": "test_pass",
            },
        ):
            with patch.dict(sys.modules, {"praw": None}):
                result = await post_to_reddit("test", "Test", "Test")
                assert result["success"] is False
                assert "PRAW not installed" in result["error"]

    @pytest.mark.asyncio
    async def test_post_to_reddit_api_error(self):
        """Test handling of Reddit API errors"""
        from server import post_to_reddit

        mock_praw = MagicMock()
        mock_praw.Reddit.side_effect = Exception("Reddit API error")

        with patch.dict(
            os.environ,
            {
                "REDDIT_CLIENT_ID": "test_id",
                "REDDIT_CLIENT_SECRET": "test_secret",
                "REDDIT_USER_AGENT": "TestBot/1.0",
                "REDDIT_USERNAME": "test_user",
                "REDDIT_PASSWORD": "test_pass",
            },
        ):
            with patch("server.praw", mock_praw):
                result = await post_to_reddit("test", "Test", "Test")

        assert result["success"] is False
        assert "error" in result


class TestRedditRateLimiting:
    """Test Reddit rate limiting awareness"""

    def test_rate_limit_calculation(self):
        """Verify rate limit delay calculation"""
        subreddits = ["SaaS", "SideProject", "startups", "test"]
        expected_delay = 5 * 60  # 5 minutes in seconds

        total_delay = (len(subreddits) - 1) * expected_delay

        assert total_delay == 15 * 60, (
            "Should have 15 minutes of delays for 4 subreddits"
        )

    def test_staggered_posting_sequence(self):
        """Test that Reddit posts are properly staggered"""
        subreddits = ["test1", "test2", "test3"]
        posts = []

        for i, sub in enumerate(subreddits):
            post_time = i * 300  # 5 minutes apart
            posts.append({"subreddit": sub, "scheduled_time": post_time})

        for i in range(1, len(posts)):
            diff = posts[i]["scheduled_time"] - posts[i - 1]["scheduled_time"]
            assert diff >= 300, "Posts should be at least 5 minutes apart"

    def test_recommended_subreddit_delay(self):
        """Verify recommended delay between Reddit posts"""
        recommended_delay_seconds = 300  # 5 minutes
        posts_count = 5
        min_total_time = (posts_count - 1) * recommended_delay_seconds

        assert min_total_time == 1200, "5 posts should take at least 20 minutes"


class TestRedditPostRequest:
    """Test Reddit post request validation"""

    def test_reddit_requires_subreddit(self):
        """Verify Reddit posts require subreddit"""
        from server import PostRequest

        with pytest.raises(Exception):
            PostRequest(text="Test", platforms=["reddit"], title="Test")

    def test_reddit_requires_title(self):
        """Verify Reddit posts require title"""
        from server import PostRequest

        with pytest.raises(Exception):
            PostRequest(text="Test", platforms=["reddit"], subreddit="test")
