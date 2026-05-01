from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.persistence import RuntimeStore
from app.runtime.schemas import RuntimeTask, TaskStatus


TaskHandler = Callable[[RuntimeTask], Awaitable[dict[str, Any]]]


class TaskManager:
    def __init__(self, store: RuntimeStore, concurrency: int = 2):
        self.store = store
        self.queue: asyncio.Queue[RuntimeTask] = asyncio.Queue()
        self.handlers: dict[str, TaskHandler] = {}
        self.concurrency = concurrency
        self._workers: list[asyncio.Task[None]] = []

    def register_handler(self, kind: str, handler: TaskHandler) -> None:
        self.handlers[kind] = handler

    async def submit(self, kind: str, payload: dict[str, Any]) -> RuntimeTask:
        task = RuntimeTask(kind=kind, payload=payload)
        self.store.upsert_task(task.id, task.kind, task.status.value, task.payload)
        await self.queue.put(task)
        return task

    def start(self) -> None:
        if self._workers:
            return
        self._workers = [
            asyncio.create_task(self._worker_loop(), name=f"agent-worker-{index}")
            for index in range(self.concurrency)
        ]

    async def stop(self) -> None:
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers = []

    async def _worker_loop(self) -> None:
        while True:
            task = await self.queue.get()
            try:
                await self._run(task)
            finally:
                self.queue.task_done()

    async def _run(self, task: RuntimeTask) -> None:
        handler = self.handlers.get(task.kind)
        if handler is None:
            error = f"No handler registered for task kind: {task.kind}"
            self.store.upsert_task(task.id, task.kind, TaskStatus.failed.value, task.payload, error=error)
            return

        self.store.upsert_task(task.id, task.kind, TaskStatus.running.value, task.payload)
        try:
            result = await handler(task)
            self.store.upsert_task(
                task.id,
                task.kind,
                TaskStatus.completed.value,
                task.payload,
                result=result,
            )
        except Exception as exc:
            self.store.upsert_task(
                task.id,
                task.kind,
                TaskStatus.failed.value,
                task.payload,
                error=str(exc),
            )
