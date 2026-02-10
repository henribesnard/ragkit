"""Async batch processor for high-throughput pipelines."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from typing import Any


class BatchProcessor:
    """Accumulates items into batches for async processing."""

    def __init__(
        self,
        process_batch_fn: Callable[[list[Any]], Awaitable[list[Any]]],
        batch_size: int = 32,
        timeout_ms: int = 100,
        queue_max_size: int = 1000,
    ) -> None:
        self.process_batch_fn = process_batch_fn
        self.batch_size = batch_size
        self.timeout_ms = timeout_ms
        self.queue: asyncio.Queue[tuple[Any, asyncio.Future]] = asyncio.Queue(
            maxsize=queue_max_size
        )
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def process(self, item: Any) -> Any:
        await self.start()
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        await self.queue.put((item, future))
        return await future

    async def _worker(self) -> None:
        while True:
            item, future = await self.queue.get()
            batch = [item]
            futures = [future]
            deadline = asyncio.get_running_loop().time() + (self.timeout_ms / 1000)

            while len(batch) < self.batch_size:
                timeout = deadline - asyncio.get_running_loop().time()
                if timeout <= 0:
                    break
                try:
                    item, future = await asyncio.wait_for(self.queue.get(), timeout=timeout)
                    batch.append(item)
                    futures.append(future)
                except asyncio.TimeoutError:
                    break

            try:
                results = await self.process_batch_fn(batch)
                for fut, result in zip(futures, results, strict=False):
                    if not fut.cancelled():
                        fut.set_result(result)
            except Exception as exc:  # noqa: BLE001
                for fut in futures:
                    if not fut.cancelled():
                        fut.set_exception(exc)
