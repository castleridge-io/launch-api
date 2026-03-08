"""
Pytest configuration and common fixtures
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        "API_KEY": "test_api_key",
        "LATE_API_KEY": "test_late_key",
        "TELEGRAM_BOT_TOKEN": "test_telegram_token",
        "REDDIT_CLIENT_ID": "test_client_id",
        "REDDIT_CLIENT_SECRET": "test_client_secret",
        "REDDIT_USER_AGENT": "test_user_agent",
        "REDDIT_USERNAME": "test_username",
        "REDDIT_PASSWORD": "test_password",
    }

    with pytest.MonkeyPatch.context() as m:
        for key, value in env_vars.items():
            m.setenv(key, value)
        yield env_vars
