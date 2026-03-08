"""
Retry Logic with Exponential Backoff
Implements robust retry mechanism for failed API calls
"""

import asyncio
import functools
import logging
from typing import Callable, Any, Optional, List, Type
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Optional[List[Type[Exception]]] = None
    retryable_status_codes: Optional[List[int]] = None


class RetryExhaustedError(Exception):
    def __init__(
        self, message: str, attempts: int, last_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


@dataclass
class RetryResult:
    success: bool
    result: Any = None
    error: Optional[str] = None
    attempts: int = 0
    total_time: float = 0.0
    platform: Optional[str] = None


def calculate_backoff_delay(attempt: int, config: RetryConfig) -> float:
    import random

    delay = min(
        config.base_delay * (config.exponential_base**attempt), config.max_delay
    )

    if config.jitter:
        delay = delay * (0.5 + random.random())

    return delay


def is_retryable_error(error: Exception, config: RetryConfig) -> bool:
    if config.retryable_exceptions:
        if isinstance(error, tuple(config.retryable_exceptions)):
            return True

    error_str = str(error).lower()
    retryable_keywords = [
        "timeout",
        "connection",
        "network",
        "temporarily",
        "rate limit",
        "service unavailable",
        "bad gateway",
        "gateway timeout",
        "too many requests",
        "internal server error",
    ]

    return any(keyword in error_str for keyword in retryable_keywords)


async def retry_async(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    platform: Optional[str] = None,
    **kwargs,
) -> RetryResult:
    if config is None:
        config = RetryConfig()

    start_time = datetime.now()
    last_error = None

    for attempt in range(config.max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            if attempt > 0:
                logger.info(
                    f"Retry succeeded on attempt {attempt + 1} for {platform or 'operation'}"
                )

            elapsed = (datetime.now() - start_time).total_seconds()
            return RetryResult(
                success=True,
                result=result,
                attempts=attempt + 1,
                total_time=elapsed,
                platform=platform,
            )

        except Exception as e:
            last_error = e
            error_str = str(e)

            if attempt < config.max_retries and is_retryable_error(e, config):
                delay = calculate_backoff_delay(attempt, config)
                logger.warning(
                    f"Attempt {attempt + 1}/{config.max_retries + 1} failed for {platform or 'operation'}: {error_str}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                break

    elapsed = (datetime.now() - start_time).total_seconds()
    error_msg = str(last_error) if last_error else "Unknown error"

    logger.error(
        f"All {config.max_retries + 1} attempts exhausted for {platform or 'operation'}: {error_msg}"
    )

    return RetryResult(
        success=False,
        error=error_msg,
        attempts=config.max_retries + 1,
        total_time=elapsed,
        platform=platform,
    )


def with_retry(config: Optional[RetryConfig] = None, platform: Optional[str] = None):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await retry_async(
                func, *args, config=config, platform=platform, **kwargs
            )
            if result.success:
                return result.result
            else:
                raise RetryExhaustedError(
                    f"Retry exhausted: {result.error}",
                    attempts=result.attempts,
                    last_error=Exception(result.error) if result.error else None,
                )

        return wrapper

    return decorator


DEFAULT_RETRY_CONFIG = RetryConfig(
    max_retries=3, base_delay=1.0, max_delay=60.0, exponential_base=2.0, jitter=True
)

AGGRESSIVE_RETRY_CONFIG = RetryConfig(
    max_retries=5, base_delay=2.0, max_delay=120.0, exponential_base=2.0, jitter=True
)

CONSERVATIVE_RETRY_CONFIG = RetryConfig(
    max_retries=2, base_delay=0.5, max_delay=10.0, exponential_base=2.0, jitter=True
)
