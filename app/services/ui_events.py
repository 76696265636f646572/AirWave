from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import WebSocket


EventPayload = dict[str, Any]
SnapshotBuilder = Callable[[str], Awaitable[EventPayload]]


class UiEventBroker:
    """Thread-safe pub/sub broadcaster for websocket UI event streams."""

    def __init__(self, snapshot_builder: SnapshotBuilder | None = None) -> None:
        self._snapshot_builder = snapshot_builder
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = threading.Lock()
        self._subscribers: set[asyncio.Queue[EventPayload]] = set()

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        with self._lock:
            self._loop = loop

    def set_snapshot_builder(self, snapshot_builder: SnapshotBuilder) -> None:
        self._snapshot_builder = snapshot_builder

    def publish(self, payload: EventPayload) -> None:
        with self._lock:
            loop = self._loop
        if loop is None:
            return
        if loop.is_closed():
            return
        loop.call_soon_threadsafe(self._publish_now, payload)

    def publish_snapshot(self, base_url: str) -> None:
        with self._lock:
            loop = self._loop
        if loop is None:
            return
        if loop.is_closed():
            return
        loop.call_soon_threadsafe(self._schedule_snapshot, base_url)

    async def add_client(self, websocket: WebSocket, base_url: str) -> asyncio.Queue[EventPayload]:
        await websocket.accept()
        queue: asyncio.Queue[EventPayload] = asyncio.Queue(maxsize=32)
        with self._lock:
            self._subscribers.add(queue)
        await self._enqueue_snapshot(queue, base_url)
        return queue

    async def remove_client(self, queue: asyncio.Queue[EventPayload]) -> None:
        with self._lock:
            self._subscribers.discard(queue)

    def _schedule_snapshot(self, base_url: str) -> None:
        loop = asyncio.get_running_loop()
        loop.create_task(self._broadcast_snapshot(base_url))

    async def _broadcast_snapshot(self, base_url: str) -> None:
        payload = await self._build_snapshot(base_url)
        self._publish_now(payload)

    async def _enqueue_snapshot(self, queue: asyncio.Queue[EventPayload], base_url: str) -> None:
        payload = await self._build_snapshot(base_url)
        queue.put_nowait(payload)

    async def _build_snapshot(self, base_url: str) -> EventPayload:
        if self._snapshot_builder is None:
            now = time.time()
            return {
                "type": "snapshot",
                "timestamp": now,
                "state": {},
            }
        snapshot = await self._snapshot_builder(base_url)
        snapshot.setdefault("type", "snapshot")
        snapshot.setdefault("timestamp", time.time())
        return snapshot

    def _publish_now(self, payload: EventPayload) -> None:
        with self._lock:
            queues = list(self._subscribers)
        for queue in queues:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                continue
