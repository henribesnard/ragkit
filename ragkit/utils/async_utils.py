"""Async helpers."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def run_with_timeout(coro: Awaitable[T], timeout: float) -> T:
    return await asyncio.wait_for(coro, timeout=timeout)


async def retry_async(
    coro_factory: Callable[[], Awaitable[T]],
    max_retries: int,
    delay: float,
) -> T:
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= max_retries - 1:
                raise
            await asyncio.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError("retry_async reached an unexpected state")


async def gather_with_concurrency(
    coros: list[Awaitable[T]],
    max_concurrent: int,
) -> list[T]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _run(coro: Awaitable[T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(_run(coro) for coro in coros))
