"""Rate limiter for per-user request quotas."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from ragkit.security.exceptions import RateLimitExceededException


@dataclass
class _Bucket:
    count: int
    window_start: float


class RateLimiter:
    """Token bucket style limiter with minute and day windows."""

    def __init__(self, max_per_minute: int, max_per_day: int) -> None:
        self.max_per_minute = max_per_minute
        self.max_per_day = max_per_day
        self._minute_bucket: dict[str, _Bucket] = {}
        self._day_bucket: dict[str, _Bucket] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, user_id: str | None) -> None:
        """Check and increment rate usage for a user."""
        key = user_id or "anonymous"
        async with self._lock:
            now = time.time()
            self._consume(self._minute_bucket, key, now, 60.0, self.max_per_minute)
            self._consume(self._day_bucket, key, now, 86400.0, self.max_per_day)

    def _consume(
        self,
        bucket: dict[str, _Bucket],
        key: str,
        now: float,
        window_seconds: float,
        limit: int,
    ) -> None:
        entry = bucket.get(key)
        if entry is None or (now - entry.window_start) >= window_seconds:
            bucket[key] = _Bucket(count=1, window_start=now)
            return

        if entry.count >= limit:
            raise RateLimitExceededException(
                f"Rate limit exceeded ({limit} per {int(window_seconds)}s)"
            )

        entry.count += 1
