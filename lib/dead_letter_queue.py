"""
Dead Letter Queue for Failed Posts
Stores and manages posts that permanently failed after all retries
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class FailedPost:
    id: str
    platform: str
    timestamp: str
    payload: Dict[str, Any]
    error: str
    attempts: int
    last_attempt: str
    recoverable: bool = True
    metadata: Optional[Dict[str, Any]] = None


class DeadLetterQueue:
    def __init__(self, storage_path: Optional[Path] = None, max_size: int = 1000):
        if storage_path is None:
            storage_path = (
                Path.home() / "launch-api" / "data" / "dead_letter_queue.json"
            )

        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
        self._lock = threading.Lock()
        self._queue: Dict[str, FailedPost] = {}

        self._load_queue()

    def _load_queue(self):
        try:
            if self.storage_path.exists():
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self._queue = {k: FailedPost(**v) for k, v in data.items()}
                logger.info(
                    f"Loaded {len(self._queue)} failed posts from dead letter queue"
                )
        except Exception as e:
            logger.error(f"Failed to load dead letter queue: {e}")
            self._queue = {}

    def _save_queue(self):
        try:
            with open(self.storage_path, "w") as f:
                json.dump({k: asdict(v) for k, v in self._queue.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save dead letter queue: {e}")

    def add(
        self,
        platform: str,
        payload: Dict[str, Any],
        error: str,
        attempts: int,
        recoverable: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        with self._lock:
            timestamp = datetime.now().isoformat()
            post_id = f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            failed_post = FailedPost(
                id=post_id,
                platform=platform,
                timestamp=timestamp,
                payload=payload,
                error=error,
                attempts=attempts,
                last_attempt=timestamp,
                recoverable=recoverable,
                metadata=metadata,
            )

            self._queue[post_id] = failed_post

            if len(self._queue) > self.max_size:
                oldest_key = min(
                    self._queue.keys(), key=lambda k: self._queue[k].timestamp
                )
                del self._queue[oldest_key]
                logger.warning(
                    f"Dead letter queue max size reached, removed oldest entry: {oldest_key}"
                )

            self._save_queue()

            logger.error(
                f"Added to dead letter queue: {platform} post failed after {attempts} attempts. "
                f"ID: {post_id}"
            )

            return post_id

    def get(self, post_id: str) -> Optional[FailedPost]:
        with self._lock:
            return self._queue.get(post_id)

    def get_all(self) -> List[FailedPost]:
        with self._lock:
            return list(self._queue.values())

    def get_by_platform(self, platform: str) -> List[FailedPost]:
        with self._lock:
            return [post for post in self._queue.values() if post.platform == platform]

    def get_recoverable(self) -> List[FailedPost]:
        with self._lock:
            return [post for post in self._queue.values() if post.recoverable]

    def remove(self, post_id: str) -> bool:
        with self._lock:
            if post_id in self._queue:
                del self._queue[post_id]
                self._save_queue()
                logger.info(f"Removed post {post_id} from dead letter queue")
                return True
            return False

    def clear(self):
        with self._lock:
            self._queue.clear()
            self._save_queue()
            logger.info("Cleared dead letter queue")

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            platform_counts = {}
            recoverable_count = 0

            for post in self._queue.values():
                platform_counts[post.platform] = (
                    platform_counts.get(post.platform, 0) + 1
                )
                if post.recoverable:
                    recoverable_count += 1

            return {
                "total": len(self._queue),
                "by_platform": platform_counts,
                "recoverable": recoverable_count,
                "non_recoverable": len(self._queue) - recoverable_count,
            }

    def retry_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        post = self.get(post_id)
        if post and post.recoverable:
            logger.info(f"Preparing retry for post {post_id}")
            self.remove(post_id)
            return post.payload
        return None


dead_letter_queue = DeadLetterQueue()
