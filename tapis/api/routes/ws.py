from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...services.bus import bus

router = APIRouter()


@router.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    q = bus.sub("event")
    qa = bus.sub("audio")
    qc = bus.sub("cell")
    try:
        while True:
            msg = await asyncio.wait_for(_gabung(q, qa, qc), timeout=25)
            await sock.send_text(json.dumps(msg, default=str))
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        bus.unsub("event", q)
        bus.unsub("audio", qa)
        bus.unsub("cell", qc)


async def _gabung(*queues):
    tasks = [asyncio.create_task(q.get()) for q in queues]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()
    return next(iter(done)).result()
