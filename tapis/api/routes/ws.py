from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...services.bus import bus

router = APIRouter()


async def _ambil(*queues):
    tugas = [asyncio.create_task(q.get()) for q in queues]
    selesai, sisa = await asyncio.wait(tugas, return_when=asyncio.FIRST_COMPLETED)
    for t in sisa:
        t.cancel()
    return next(iter(selesai)).result()


@router.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    qs = [bus.sub(k) for k in ("event", "audio", "cell")]
    try:
        while True:
            await sock.send_text(json.dumps(await asyncio.wait_for(_ambil(*qs), 25), default=str))
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        for k, q in zip(("event", "audio", "cell"), qs):
            bus.unsub(k, q)
