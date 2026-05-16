from __future__ import annotations

import asyncio

from comfyui_tg_bot.models import GenerationJob


class GenerationQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[GenerationJob] = asyncio.Queue()

    async def enqueue(self, job: GenerationJob) -> None:
        await self._queue.put(job)

    async def get(self) -> GenerationJob:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    def size(self) -> int:
        return self._queue.qsize()
