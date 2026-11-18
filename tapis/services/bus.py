from __future__ import annotations

import asyncio
from collections import defaultdict


class Bus:
    def __init__(self) -> None:
        self._subs: dict[str, set[asyncio.Queue]] = defaultdict(set)

    def sub(self, topik: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=512)
        self._subs[topik].add(q)
        return q

    def unsub(self, topik: str, q: asyncio.Queue) -> None:
        self._subs[topik].discard(q)

    async def pub(self, topik: str, msg: dict) -> None:
        for q in list(self._subs[topik]):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass


bus = Bus()
