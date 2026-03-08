"""
Error Logging and User-Friendly Error Messages
Provides detailed logging and human-readable error messages
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import traceback

logger = logging.getLogger(__name__)


@dataclass
class ErrorLog:
    timestamp: str
    platform: str
    error_type: str
    error_message: str
    error_details: str
    user_message: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None


USER_FRIENDLY_MESSAGES = {
    "twitter": {
        "rate_limit": "Twitter rate limit reached. Please wait a few minutes before posting again.",
        "auth_failed": "Twitter authentication failed. Please check your API credentials.",
        "network_error": "Unable to connect to Twitter. Please check your internet connection.",
        "invalid_media": "The media file for Twitter is invalid or too large.",
        "duplicate": "This tweet appears to be a duplicate of a recent post.",
        "default": "Failed to post to Twitter. Please try again later.",
    },
    "linkedin": {
        "rate_limit": "LinkedIn posting limit reached. Please wait before posting again.",
        "auth_failed": "LinkedIn authentication failed. Please check your API credentials.",
        "network_error": "Unable to connect to LinkedIn. Please check your internet connection.",
        "invalid_media": "The media file for LinkedIn is invalid or not supported.",
        "default": "Failed to post to LinkedIn. Please try again later.",
    },
    "facebook": {
        "rate_limit": "Facebook rate limit reached. Please wait before posting again.",
        "auth_failed": "Facebook authentication failed. Please check your API credentials.",
        "network_error": "Unable to connect to Facebook. Please check your internet connection.",
        "invalid_media": "The media file for Facebook is invalid or too large.",
        "default": "Failed to post to Facebook. Please try again later.",
    },
    "instagram": {
        "rate_limit": "Instagram posting limit reached. Please wait before posting again.",
        "auth_failed": "Instagram authentication failed. Please check your API credentials.",
        "network_error": "Unable to connect to Instagram. Please check your internet connection.",
        "invalid_media": "The media file for Instagram is invalid or doesn't meet requirements.",
        "default": "Failed to post to Instagram. Please try again later.",
    },
    "reddit": {
        "rate_limit": "Reddit rate limit reached. Please wait before posting again.",
        "auth_failed": "Reddit authentication failed. Please check your Reddit credentials.",
        "network_error": "Unable to connect to Reddit. Please check your internet connection.",
        "subreddit_not_found": "The specified subreddit does not exist or you don't have access.",
        "banned": "Your account has been banned from this subreddit.",
        "duplicate": "This post has already been submitted to this subreddit.",
        "default": "Failed to post to Reddit. Please try again later.",
    },
    "telegram": {
        "rate_limit": "Telegram rate limit reached. Please wait before posting again.",
        "auth_failed": "Telegram bot authentication failed. Please check your bot token.",
        "network_error": "Unable to connect to Telegram. Please check your internet connection.",
        "channel_not_found": "The specified Telegram channel does not exist or the bot doesn't have access.",
        "default": "Failed to post to Telegram. Please try again later.",
    },
    "discord": {
        "rate_limit": "Discord rate limit reached. Please wait before posting again.",
        "auth_failed": "Discord webhook authentication failed. Please check the webhook URL.",
        "network_error": "Unable to connect to Discord. Please check your internet connection.",
        "invalid_webhook": "The Discord webhook URL is invalid or has been deleted.",
        "default": "Failed to post to Discord. Please try again later.",
    },
    "slack": {
        "rate_limit": "Slack rate limit reached. Please wait before posting again.",
        "auth_failed": "Slack webhook authentication failed. Please check the webhook URL.",
        "network_error": "Unable to connect to Slack. Please check your internet connection.",
        "invalid_webhook": "The Slack webhook URL is invalid or has been disabled.",
        "default": "Failed to post to Slack. Please try again later.",
    },
    "late_dev": {
        "rate_limit": "Late.dev API rate limit reached. Please wait before posting again.",
        "auth_failed": "Late.dev authentication failed. Please check your API key.",
        "network_error": "Unable to connect to Late.dev. Please check your internet connection.",
        "quota_exceeded": "Late.dev API quota exceeded. Please upgrade your plan.",
        "default": "Failed to post via Late.dev. Please try again later.",
    },
}


def classify_error(error: Exception, platform: str) -> str:
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()

    if "rate" in error_str or "limit" in error_str or "429" in error_str:
        return "rate_limit"
    elif (
        "auth" in error_str
        or "unauthorized" in error_str
        or "401" in error_str
        or "403" in error_str
    ):
        return "auth_failed"
    elif "timeout" in error_str or "connection" in error_str or "network" in error_str:
        return "network_error"
    elif "not found" in error_str or "404" in error_str:
        return "not_found"
    elif (
        "media" in error_str
        or "file" in error_str
        or "image" in error_str
        or "video" in error_str
    ):
        return "invalid_media"
    elif "duplicate" in error_str:
        return "duplicate"
    elif "banned" in error_str:
        return "banned"
    elif "subreddit" in error_str:
        return "subreddit_not_found"
    elif "channel" in error_str:
        return "channel_not_found"
    elif "webhook" in error_str:
        return "invalid_webhook"
    elif "quota" in error_str:
        return "quota_exceeded"
    else:
        return "default"


def get_user_friendly_message(platform: str, error_type: str) -> str:
    platform_messages = USER_FRIENDLY_MESSAGES.get(platform.lower(), {})
    return platform_messages.get(
        error_type, f"Failed to post to {platform}. Please try again later."
    )


class ErrorLogger:
    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir is None:
            log_dir = Path.home() / "launch-api" / "logs" / "errors"

        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.current_log_file = (
            self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )

    def log_error(
        self,
        platform: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        include_stack_trace: bool = True,
    ) -> ErrorLog:
        error_type = classify_error(error, platform)
        user_message = get_user_friendly_message(platform, error_type)

        error_log = ErrorLog(
            timestamp=datetime.now().isoformat(),
            platform=platform,
            error_type=error_type,
            error_message=str(error),
            error_details=repr(error),
            user_message=user_message,
            context=context or {},
            stack_trace=traceback.format_exc() if include_stack_trace else None,
        )

        self._write_log(error_log)

        logger.error(
            f"[{platform.upper()}] {error_type}: {error_log.error_message}",
            extra={"context": context},
        )

        return error_log

    def _write_log(self, error_log: ErrorLog):
        try:
            with open(self.current_log_file, "a") as f:
                f.write(json.dumps(asdict(error_log)) + "\n")
        except Exception as e:
            logger.error(f"Failed to write error log: {e}")

    def get_recent_errors(
        self, platform: Optional[str] = None, limit: int = 100
    ) -> List[ErrorLog]:
        errors = []

        try:
            if self.current_log_file.exists():
                with open(self.current_log_file, "r") as f:
                    for line in f:
                        try:
                            error_data = json.loads(line.strip())
                            error_log = ErrorLog(**error_data)

                            if platform is None or error_log.platform == platform:
                                errors.append(error_log)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Failed to read error logs: {e}")

        return errors[-limit:]


error_logger = ErrorLogger()
