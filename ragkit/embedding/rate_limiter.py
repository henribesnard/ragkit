"""Rate limiter for respecting API quotas (RPM/TPM)."""

from __future__ import annotations

import asyncio
import time


class RateLimiter:
    """Rate limiter for API quotas (Requests Per Minute / Tokens Per Minute).

    Manages two types of limits:
    - RPM: Number of requests per minute
    - TPM: Number of tokens per minute

    Example:
        limiter = RateLimiter(rpm=3000, tpm=1_000_000)
        await limiter.acquire(tokens=500)  # Waits if quota exceeded
    """

    def __init__(self, rpm: int | None, tpm: int | None) -> None:
        """Initialize the rate limiter.

        Args:
            rpm: Requests per minute (None = no limit)
            tpm: Tokens per minute (None = no limit)
        """
        self.rpm = rpm
        self.tpm = tpm

        # Request history (timestamps)
        self.request_times: list[float] = []

        # Token counter
        self.token_count = 0
        self.last_reset = time.time()

    async def acquire(self, tokens: int = 1) -> None:
        """Wait if necessary to respect RPM/TPM limits.

        Args:
            tokens: Number of tokens for this request
        """
        now = time.time()

        # Reset every 60 seconds
        if now - self.last_reset >= 60:
            self.request_times = []
            self.token_count = 0
            self.last_reset = now

        # Check RPM (Requests Per Minute)
        if self.rpm is not None:
            # Filter requests from last 60 seconds
            self.request_times = [t for t in self.request_times if now - t < 60]

            if len(self.request_times) >= self.rpm:
                # Quota reached, wait
                wait_time = 60 - (now - self.request_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Recalculate now after sleep
                    now = time.time()
                    self.request_times = []
                    self.token_count = 0
                    self.last_reset = now

        # Check TPM (Tokens Per Minute)
        if self.tpm is not None and self.token_count + tokens > self.tpm:
            # Token quota exceeded, wait until end of minute
            wait_time = 60 - (now - self.last_reset)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self.token_count = 0
                self.last_reset = time.time()
                self.request_times = []

        # Register this request
        self.request_times.append(time.time())
        self.token_count += tokens
