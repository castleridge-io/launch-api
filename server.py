"""
Launch API Server
Hybrid: Late.dev for hard platforms, direct API for easy ones
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import requests
from dotenv import load_dotenv
import logging
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.retry import retry_async, RetryConfig, RetryResult
from lib.dead_letter_queue import dead_letter_queue
from lib.error_logging import error_logger

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Launch API", description="Unified social media posting API", version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
API_KEY = os.getenv("API_KEY", "dev_key")
LATE_API_KEY = os.getenv("LATE_API_KEY")

# ============================================
# Models
# ============================================


class PostRequest(BaseModel):
    text: str
    platforms: List[str]
    mediaUrls: Optional[List[str]] = []

    # Platform-specific
    subreddit: Optional[str] = None  # Reddit
    title: Optional[str] = None  # Reddit
    channel_id: Optional[str] = None  # Telegram
    webhooks: Optional[List[str]] = []  # Discord/Slack


class PostResponse(BaseModel):
    success: bool
    platform: str
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    user_message: Optional[str] = None
    attempts: Optional[int] = None


# ============================================
# Auth
# ============================================


def verify_api_key(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API key")

    key = authorization.replace("Bearer ", "")
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


# ============================================
# Late.dev Proxy (Hard Platforms)
# ============================================

LATE_PLATFORMS = [
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


async def _post_via_late_internal(
    text: str, platforms: List[str], media_urls: List[str] = None
):
    """Internal Late.dev posting function (without retry)"""
    if not LATE_API_KEY:
        raise ValueError("Late API key not configured")

    late_platforms = [p for p in platforms if p in LATE_PLATFORMS]
    if not late_platforms:
        raise ValueError("No Late-supported platforms")

    url = "https://getlate.dev/api/v1/posts"

    payload = {"text": text, "platforms": late_platforms, "mediaUrls": media_urls or []}

    headers = {
        "Authorization": f"Bearer {LATE_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise Exception(f"Late API error: {response.status_code} - {response.text}")


async def post_via_late(text: str, platforms: List[str], media_urls: List[str] = None):
    """Post to hard platforms via Late.dev with retry logic"""
    try:
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=2.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=True,
        )

        result = await retry_async(
            _post_via_late_internal,
            text,
            platforms,
            media_urls,
            config=retry_config,
            platform="late_dev",
        )

        if result.success:
            return result.result
        else:
            error = Exception(result.error)
            error_logger.log_error(
                "late_dev",
                error,
                context={"platforms": platforms, "text_length": len(text)},
            )
            return {
                "success": False,
                "error": result.error,
                "attempts": result.attempts,
            }

    except Exception as e:
        error_logger.log_error(
            "late_dev", e, context={"platforms": platforms, "text_length": len(text)}
        )
        return {"success": False, "error": str(e), "attempts": 1}


# ============================================
# Reddit (Easy - Direct API)
# ============================================


async def _post_to_reddit_internal(subreddit: str, title: str, text: str):
    """Internal Reddit posting function (without retry)"""
    import praw

    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
    )

    subreddit_obj = reddit.subreddit(subreddit)
    submission = subreddit_obj.submit(title, selftext=text)

    return {
        "success": True,
        "platform": "reddit",
        "post_id": submission.id,
        "url": f"https://reddit.com{submission.permalink}",
    }


async def post_to_reddit(subreddit: str, title: str, text: str):
    """Post to Reddit via PRAW with retry logic"""
    try:
        import praw
    except ImportError:
        error = ImportError("PRAW not installed. Run: pip install praw")
        error_log = error_logger.log_error(
            "reddit", error, context={"subreddit": subreddit}
        )
        return {
            "success": False,
            "platform": "reddit",
            "error": error_log.user_message,
            "attempts": 0,
        }

    try:
        retry_config = RetryConfig(
            max_retries=2,
            base_delay=5.0,
            max_delay=120.0,
            exponential_base=2.0,
            jitter=True,
        )

        result = await retry_async(
            _post_to_reddit_internal,
            subreddit,
            title,
            text,
            config=retry_config,
            platform="reddit",
        )

        if result.success:
            return result.result
        else:
            error = Exception(result.error)
            error_log = error_logger.log_error(
                "reddit", error, context={"subreddit": subreddit, "title": title}
            )

            dead_letter_queue.add(
                platform="reddit",
                payload={"subreddit": subreddit, "title": title, "text": text},
                error=result.error,
                attempts=result.attempts,
                recoverable=True,
            )

            return {
                "success": False,
                "platform": "reddit",
                "error": error_log.user_message,
                "attempts": result.attempts,
            }

    except Exception as e:
        error_log = error_logger.log_error(
            "reddit", e, context={"subreddit": subreddit}
        )
        return {
            "success": False,
            "platform": "reddit",
            "error": error_log.user_message,
            "attempts": 1,
        }


# ============================================
# Telegram (Easy - Bot API)
# ============================================


async def _post_to_telegram_internal(
    channel_id: str, text: str, parse_mode: str = "Markdown"
):
    """Internal Telegram posting function (without retry)"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        raise ValueError("Telegram bot token not configured")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {"chat_id": channel_id, "text": text, "parse_mode": parse_mode}

    response = requests.post(url, json=payload, timeout=10)

    if response.status_code == 200:
        data = response.json()
        return {
            "success": True,
            "platform": "telegram",
            "post_id": str(data["result"]["message_id"]),
            "url": f"https://t.me/c/{channel_id.replace('@', '').replace('-100', '')}/{data['result']['message_id']}",
        }
    else:
        raise Exception(f"Telegram API error: {response.status_code} - {response.text}")


async def post_to_telegram(channel_id: str, text: str, parse_mode: str = "Markdown"):
    """Post to Telegram via Bot API with retry logic"""
    try:
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=2.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True,
        )

        result = await retry_async(
            _post_to_telegram_internal,
            channel_id,
            text,
            parse_mode,
            config=retry_config,
            platform="telegram",
        )

        if result.success:
            return result.result
        else:
            error = Exception(result.error)
            error_log = error_logger.log_error(
                "telegram", error, context={"channel_id": channel_id}
            )

            dead_letter_queue.add(
                platform="telegram",
                payload={
                    "channel_id": channel_id,
                    "text": text,
                    "parse_mode": parse_mode,
                },
                error=result.error or "Unknown error",
                attempts=result.attempts,
                recoverable=True,
            )

            return {
                "success": False,
                "platform": "telegram",
                "error": error_log.user_message,
                "attempts": result.attempts,
            }

    except Exception as e:
        error_log = error_logger.log_error(
            "telegram", e, context={"channel_id": channel_id}
        )
        return {
            "success": False,
            "platform": "telegram",
            "error": error_log.user_message,
            "attempts": 1,
        }


# ============================================
# Discord (Easy - Webhooks)
# ============================================


async def _post_to_discord_internal(webhook_url: str, text: str):
    """Internal Discord posting function (without retry)"""
    payload = {"content": text, "username": "Launch Bot"}

    response = requests.post(webhook_url, json=payload, timeout=10)

    if response.status_code == 204:
        return {"success": True, "platform": "discord"}
    else:
        raise Exception(
            f"Discord webhook error: {response.status_code} - {response.text}"
        )


async def post_to_discord(webhook_url: str, text: str):
    """Post to Discord via webhook with retry logic"""
    try:
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=20.0,
            exponential_base=2.0,
            jitter=True,
        )

        result = await retry_async(
            _post_to_discord_internal,
            webhook_url,
            text,
            config=retry_config,
            platform="discord",
        )

        if result.success:
            return result.result
        else:
            error = Exception(result.error)
            error_log = error_logger.log_error(
                "discord", error, context={"webhook_url": webhook_url[:30] + "..."}
            )

            dead_letter_queue.add(
                platform="discord",
                payload={"webhook_url": webhook_url, "text": text},
                error=result.error or "Unknown error",
                attempts=result.attempts,
                recoverable=True,
            )

            return {
                "success": False,
                "platform": "discord",
                "error": error_log.user_message,
                "attempts": result.attempts,
            }

    except Exception as e:
        error_log = error_logger.log_error(
            "discord", e, context={"webhook_url": webhook_url[:30] + "..."}
        )
        return {
            "success": False,
            "platform": "discord",
            "error": error_log.user_message,
            "attempts": 1,
        }


# ============================================
# Slack (Easy - Webhooks)
# ============================================


async def _post_to_slack_internal(webhook_url: str, text: str):
    """Internal Slack posting function (without retry)"""
    payload = {"text": text, "username": "Launch Bot", "icon_emoji": ":rocket:"}

    response = requests.post(webhook_url, json=payload, timeout=10)

    if response.status_code == 200:
        return {"success": True, "platform": "slack"}
    else:
        raise Exception(
            f"Slack webhook error: {response.status_code} - {response.text}"
        )


async def post_to_slack(webhook_url: str, text: str):
    """Post to Slack via webhook with retry logic"""
    try:
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=20.0,
            exponential_base=2.0,
            jitter=True,
        )

        result = await retry_async(
            _post_to_slack_internal,
            webhook_url,
            text,
            config=retry_config,
            platform="slack",
        )

        if result.success:
            return result.result
        else:
            error = Exception(result.error)
            error_log = error_logger.log_error(
                "slack", error, context={"webhook_url": webhook_url[:30] + "..."}
            )

            dead_letter_queue.add(
                platform="slack",
                payload={"webhook_url": webhook_url, "text": text},
                error=result.error or "Unknown error",
                attempts=result.attempts,
                recoverable=True,
            )

            return {
                "success": False,
                "platform": "slack",
                "error": error_log.user_message,
                "attempts": result.attempts,
            }

    except Exception as e:
        error_log = error_logger.log_error(
            "slack", e, context={"webhook_url": webhook_url[:30] + "..."}
        )
        return {
            "success": False,
            "platform": "slack",
            "error": error_log.user_message,
            "attempts": 1,
        }


# ============================================
# API Endpoints
# ============================================


@app.get("/")
async def root():
    return {
        "service": "Launch API",
        "version": "1.0.0",
        "platforms": {
            "late_dev": LATE_PLATFORMS,
            "direct": ["reddit", "telegram", "discord", "slack"],
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/post", response_model=List[PostResponse])
async def create_post(post: PostRequest, authorization: str = Header(None)):
    """Post to multiple platforms"""
    verify_api_key(authorization)

    results = []

    # 1. Late.dev platforms (Twitter, LinkedIn, Facebook, Instagram, TikTok, etc.)
    late_platforms = [p for p in post.platforms if p in LATE_PLATFORMS]
    if late_platforms:
        late_result = await post_via_late(post.text, late_platforms, post.mediaUrls)
        if late_result.get("success") != False:
            for platform in late_platforms:
                results.append(
                    PostResponse(
                        success=True,
                        platform=platform,
                        post_id=late_result.get("id"),
                        url=late_result.get("url"),
                    )
                )
        else:
            for platform in late_platforms:
                results.append(
                    PostResponse(
                        success=False, platform=platform, error=late_result.get("error")
                    )
                )

    # 2. Reddit
    if "reddit" in post.platforms:
        if not post.subreddit or not post.title:
            results.append(
                PostResponse(
                    success=False,
                    platform="reddit",
                    error="Reddit requires 'subreddit' and 'title' fields",
                )
            )
        else:
            reddit_result = await post_to_reddit(post.subreddit, post.title, post.text)
            results.append(PostResponse(**reddit_result))

    # 3. Telegram
    if "telegram" in post.platforms:
        if not post.channel_id:
            results.append(
                PostResponse(
                    success=False,
                    platform="telegram",
                    error="Telegram requires 'channel_id' field",
                )
            )
        else:
            telegram_result = await post_to_telegram(post.channel_id, post.text)
            results.append(PostResponse(**telegram_result))

    # 4. Discord
    if "discord" in post.platforms:
        for webhook_url in post.webhooks:
            discord_result = await post_to_discord(webhook_url, post.text)
            results.append(PostResponse(**discord_result))

    # 5. Slack
    if "slack" in post.platforms:
        for webhook_url in post.webhooks:
            slack_result = await post_to_slack(webhook_url, post.text)
            results.append(PostResponse(**slack_result))

    return results


# ============================================
# Platform-Specific Endpoints
# ============================================


@app.post("/reddit")
async def reddit_only(
    subreddit: str, title: str, text: str, authorization: str = Header(None)
):
    """Post to Reddit only"""
    verify_api_key(authorization)
    result = await post_to_reddit(subreddit, title, text)
    return PostResponse(**result)


@app.post("/telegram")
async def telegram_only(channel_id: str, text: str, authorization: str = Header(None)):
    """Post to Telegram only"""
    verify_api_key(authorization)
    result = await post_to_telegram(channel_id, text)
    return PostResponse(**result)


@app.post("/discord")
async def discord_only(webhook_url: str, text: str, authorization: str = Header(None)):
    """Post to Discord only"""
    verify_api_key(authorization)
    result = await post_to_discord(webhook_url, text)
    return PostResponse(**result)


@app.post("/slack")
async def slack_only(webhook_url: str, text: str, authorization: str = Header(None)):
    """Post to Slack only"""
    verify_api_key(authorization)
    result = await post_to_slack(webhook_url, text)
    return PostResponse(**result)


# ============================================
# Dead Letter Queue Management Endpoints
# ============================================


@app.get("/dead-letter-queue/stats")
async def get_dlq_stats(authorization: str = Header(None)):
    """Get dead letter queue statistics"""
    verify_api_key(authorization)
    return dead_letter_queue.stats()


@app.get("/dead-letter-queue")
async def get_dlq_posts(
    platform: Optional[str] = None, authorization: str = Header(None)
):
    """Get failed posts from dead letter queue"""
    verify_api_key(authorization)

    if platform:
        posts = dead_letter_queue.get_by_platform(platform)
    else:
        posts = dead_letter_queue.get_all()

    return {"total": len(posts), "posts": [post.__dict__ for post in posts]}


@app.delete("/dead-letter-queue/{post_id}")
async def remove_from_dlq(post_id: str, authorization: str = Header(None)):
    """Remove a post from the dead letter queue"""
    verify_api_key(authorization)

    if dead_letter_queue.remove(post_id):
        return {"success": True, "message": f"Post {post_id} removed"}
    else:
        raise HTTPException(status_code=404, detail="Post not found")


@app.post("/dead-letter-queue/{post_id}/retry")
async def retry_dlq_post(post_id: str, authorization: str = Header(None)):
    """Retry a failed post from the dead letter queue"""
    verify_api_key(authorization)

    payload = dead_letter_queue.retry_post(post_id)
    if payload:
        return {
            "success": True,
            "payload": payload,
            "message": "Post removed from queue for retry",
        }
    else:
        raise HTTPException(status_code=404, detail="Post not found or not recoverable")


@app.get("/errors")
async def get_recent_errors(
    platform: Optional[str] = None, limit: int = 100, authorization: str = Header(None)
):
    """Get recent error logs"""
    verify_api_key(authorization)

    errors = error_logger.get_recent_errors(platform=platform, limit=limit)
    return {"total": len(errors), "errors": [error.__dict__ for error in errors]}


# ============================================
# Run
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
    )
