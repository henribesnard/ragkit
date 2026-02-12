"""Tests for rate limiting."""

import pytest

from ragkit.security.exceptions import RateLimitExceededException
from ragkit.security.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limit_enforced():
    limiter = RateLimiter(max_per_minute=5, max_per_day=100)

    for _ in range(5):
        await limiter.check_rate_limit("user123")

    with pytest.raises(RateLimitExceededException):
        await limiter.check_rate_limit("user123")
