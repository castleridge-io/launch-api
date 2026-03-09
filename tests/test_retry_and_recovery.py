"""
Unit Tests for Retry Logic and Error Recovery
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.retry import (
    retry_async,
    RetryConfig,
    RetryResult,
    RetryExhaustedError,
    calculate_backoff_delay,
    is_retryable_error,
)
from lib.dead_letter_queue import DeadLetterQueue, FailedPost
from lib.error_logging import ErrorLogger, classify_error, get_user_friendly_message


class TestRetryLogic:
    """Tests for retry functionality"""

    @pytest.mark.asyncio
    async def test_successful_function_no_retry(self):
        """Test that successful functions don't retry"""
        call_count = 0

        async def successful_func():
            nonlocal call_count
            call_count += 1
            return {"success": True}

        config = RetryConfig(max_retries=3)
        result = await retry_async(success_func, config=config)

        assert result.success is True
        assert result.attempts == 1
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_retryable_error(self):
        """Test that retryable errors trigger retries"""
        call_count = 0

        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network timeout")
            return {"success": True}

        config = RetryConfig(max_retries=3, base_delay=0.1, jitter=False)
        result = await retry_async(failing_then_success, config=config)

        assert result.success is True
        assert result.attempts == 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self):
        """Test that retries stop after max attempts"""
        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Network timeout")

        config = RetryConfig(max_retries=2, base_delay=0.1, jitter=False)
        result = await retry_async(always_fail, config=config)

        assert result.success is False
        assert result.attempts == 3
        assert "Network timeout" in result.error
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_error_no_retry(self):
        """Test that non-retryable errors don't trigger retries"""
        call_count = 0

        async def non_retryable_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid parameter")

        config = RetryConfig(max_retries=3, base_delay=0.1)
        result = await retry_async(non_retryable_error, config=config)

        assert result.success is False
        assert result.attempts == 1
        assert call_count == 1

    def test_calculate_backoff_delay(self):
        """Test exponential backoff calculation"""
        config = RetryConfig(
            base_delay=1.0, max_delay=60.0, exponential_base=2.0, jitter=False
        )

        assert calculate_backoff_delay(0, config) == 1.0
        assert calculate_backoff_delay(1, config) == 2.0
        assert calculate_backoff_delay(2, config) == 4.0
        assert calculate_backoff_delay(3, config) == 8.0

    def test_backoff_delay_with_jitter(self):
        """Test that jitter adds randomness to delay"""
        config = RetryConfig(
            base_delay=1.0, max_delay=60.0, exponential_base=2.0, jitter=True
        )

        delays = [calculate_backoff_delay(1, config) for _ in range(10)]

        assert all(1.0 < d < 4.0 for d in delays)
        assert len(set(delays)) > 1

    def test_backoff_delay_max_cap(self):
        """Test that backoff delay is capped at max_delay"""
        config = RetryConfig(
            base_delay=1.0, max_delay=10.0, exponential_base=2.0, jitter=False
        )

        assert calculate_backoff_delay(10, config) == 10.0
        assert calculate_backoff_delay(20, config) == 10.0

    def test_is_retryable_error(self):
        """Test error classification for retryability"""
        config = RetryConfig()

        assert is_retryable_error(ConnectionError("timeout"), config) is True
        assert is_retryable_error(Exception("network error"), config) is True
        assert is_retryable_error(Exception("rate limit exceeded"), config) is True
        assert is_retryable_error(Exception("service unavailable"), config) is True

        assert is_retryable_error(ValueError("invalid parameter"), config) is False
        assert is_retryable_error(KeyError("missing key"), config) is False


class TestDeadLetterQueue:
    """Tests for dead letter queue functionality"""

    @pytest.fixture
    def temp_queue(self, tmp_path):
        """Create a temporary dead letter queue for testing"""
        queue_path = tmp_path / "test_dlq.json"
        return DeadLetterQueue(storage_path=queue_path)

    def test_add_failed_post(self, temp_queue):
        """Test adding a failed post to the queue"""
        post_id = temp_queue.add(
            platform="twitter",
            payload={"text": "Test tweet"},
            error="API error",
            attempts=3,
        )

        assert post_id is not None
        assert temp_queue.size() == 1

        post = temp_queue.get(post_id)
        assert post is not None
        assert post.platform == "twitter"
        assert post.error == "API error"
        assert post.attempts == 3

    def test_get_by_platform(self, temp_queue):
        """Test retrieving posts by platform"""
        temp_queue.add("twitter", {"text": "Tweet 1"}, "Error 1", 3)
        temp_queue.add("twitter", {"text": "Tweet 2"}, "Error 2", 3)
        temp_queue.add("reddit", {"text": "Post 1"}, "Error 3", 2)

        twitter_posts = temp_queue.get_by_platform("twitter")
        reddit_posts = temp_queue.get_by_platform("reddit")

        assert len(twitter_posts) == 2
        assert len(reddit_posts) == 1

    def test_remove_post(self, temp_queue):
        """Test removing a post from the queue"""
        post_id = temp_queue.add("twitter", {"text": "Test"}, "Error", 3)

        assert temp_queue.size() == 1

        result = temp_queue.remove(post_id)
        assert result is True
        assert temp_queue.size() == 0

        result = temp_queue.remove("nonexistent")
        assert result is False

    def test_get_recoverable_posts(self, temp_queue):
        """Test retrieving only recoverable posts"""
        temp_queue.add("twitter", {"text": "Tweet 1"}, "Error 1", 3, recoverable=True)
        temp_queue.add("twitter", {"text": "Tweet 2"}, "Error 2", 3, recoverable=False)
        temp_queue.add("reddit", {"text": "Post 1"}, "Error 3", 2, recoverable=True)

        recoverable = temp_queue.get_recoverable()

        assert len(recoverable) == 2
        assert all(post.recoverable for post in recoverable)

    def test_queue_statistics(self, temp_queue):
        """Test queue statistics generation"""
        temp_queue.add("twitter", {"text": "Tweet 1"}, "Error 1", 3, recoverable=True)
        temp_queue.add("twitter", {"text": "Tweet 2"}, "Error 2", 3, recoverable=False)
        temp_queue.add("reddit", {"text": "Post 1"}, "Error 3", 2, recoverable=True)

        stats = temp_queue.stats()

        assert stats["total"] == 3
        assert stats["by_platform"]["twitter"] == 2
        assert stats["by_platform"]["reddit"] == 1
        assert stats["recoverable"] == 2
        assert stats["non_recoverable"] == 1

    def test_max_size_limit(self, tmp_path):
        """Test that queue respects max size limit"""
        queue_path = tmp_path / "test_dlq.json"
        queue = DeadLetterQueue(storage_path=queue_path, max_size=3)

        for i in range(5):
            queue.add("twitter", {"text": f"Tweet {i}"}, f"Error {i}", 3)

        assert queue.size() == 3


class TestErrorLogging:
    """Tests for error logging functionality"""

    @pytest.fixture
    def temp_logger(self, tmp_path):
        """Create a temporary error logger for testing"""
        log_dir = tmp_path / "logs"
        return ErrorLogger(log_dir=log_dir)

    def test_classify_error(self):
        """Test error classification"""
        assert (
            classify_error(Exception("rate limit exceeded"), "twitter") == "rate_limit"
        )
        assert classify_error(Exception("401 unauthorized"), "reddit") == "auth_failed"
        assert (
            classify_error(Exception("connection timeout"), "telegram")
            == "network_error"
        )
        assert classify_error(Exception("not found 404"), "discord") == "not_found"
        assert classify_error(Exception("unknown error"), "slack") == "default"

    def test_get_user_friendly_message(self):
        """Test user-friendly error messages"""
        msg = get_user_friendly_message("twitter", "rate_limit")
        assert "Twitter" in msg
        assert "rate limit" in msg.lower()

        msg = get_user_friendly_message("reddit", "auth_failed")
        assert "Reddit" in msg
        assert "authentication" in msg.lower()

        msg = get_user_friendly_message("unknown_platform", "default")
        assert "Failed to post" in msg

    def test_log_error(self, temp_logger):
        """Test error logging"""
        error = Exception("Test error")
        error_log = temp_logger.log_error("twitter", error, context={"tweet_id": "123"})

        assert error_log.platform == "twitter"
        assert error_log.error_message == "Test error"
        assert error_log.context == {"tweet_id": "123"}
        assert error_log.user_message is not None
        assert error_log.timestamp is not None

    def test_get_recent_errors(self, temp_logger):
        """Test retrieving recent errors"""
        temp_logger.log_error("twitter", Exception("Error 1"), context={})
        temp_logger.log_error("reddit", Exception("Error 2"), context={})
        temp_logger.log_error("twitter", Exception("Error 3"), context={})

        all_errors = temp_logger.get_recent_errors()
        assert len(all_errors) == 3

        twitter_errors = temp_logger.get_recent_errors(platform="twitter")
        assert len(twitter_errors) == 2

        reddit_errors = temp_logger.get_recent_errors(platform="reddit")
        assert len(reddit_errors) == 1


class TestIntegration:
    """Integration tests for retry + error logging + dead letter queue"""

    @pytest.mark.asyncio
    async def test_failed_post_goes_to_dlq(self, tmp_path):
        """Test that permanently failed posts end up in dead letter queue"""
        from lib.dead_letter_queue import dead_letter_queue
        from lib.error_logging import error_logger

        queue_path = tmp_path / "test_dlq.json"
        dead_letter_queue.storage_path = queue_path
        dead_letter_queue._queue = {}

        log_dir = tmp_path / "logs"
        error_logger.log_dir = log_dir
        error_logger.current_log_file = (
            log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )

        async def always_fail():
            raise ConnectionError("Network timeout")

        config = RetryConfig(max_retries=2, base_delay=0.1)
        result = await retry_async(always_fail, config=config, platform="test_platform")

        assert result.success is False
        assert result.attempts == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
