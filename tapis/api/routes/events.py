from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from ... import chain, db
from ...adapters import hi2hi3
from ...core import msisdn
from ...services import berita_acara
from ...services.bus import bus
from ..deps import wajib_token

router = APIRouter(tags=["events"], dependencies=[Depends(wajib_token)])


async def _simpan(target_id: str, body: dict) -> dict:
    with db.koneksi() as conn:
        if not conn.execute("SELECT 1 FROM target WHERE id=?", (target_id,)).fetchone():
            raise HTTPException(404, "target tidak ditemukan")
    rec = {
        "jenis": body.get("jenis", "IRI"),
        "correlation_id": body.get("correlation_id") or str(uuid.uuid4()),
        "terjadi_pada": body.get("terjadi_pada") or datetime.now(timezone.utc).isoformat(),
        "diterima_pada": datetime.now(timezone.utc).isoformat(),
        "payload": json.dumps(body.get("payload") or body, default=str),
    }
    c = chain.append(target_id, rec)
    with db.koneksi() as conn:
        cur = conn.execute(
            """INSERT INTO event(target_id,correlation_id,jenis,terjadi_pada,diterima_pada,
                   payload,hash,prev_hash) VALUES (?,?,?,?,?,?,?,?)""",
            (target_id, rec["correlation_id"], rec["jenis"], rec["terjadi_pada"],
             rec["diterima_pada"], rec["payload"], c["hash"], c["prev_hash"]),
        )
    out = {"id": cur.lastrowid, **rec, **c}
    await bus.pub("event", {"target_id": target_id, "event": out})
    return out


@router.post("/targets/{target_id}/events", status_code=201)
async def tambah(target_id: str, body: dict):
    return await _simpan(target_id, body)


@router.get("/targets/{target_id}/events")
async def daftar(target_id: str, limit: int = 200):
    with db.koneksi() as conn:
        rows = conn.execute("SELECT * FROM event WHERE target_id=? ORDER BY id DESC LIMIT ?",
                            (target_id, limit)).fetchall()
    return [dict(r) for r in rows]


@router.post("/ingest/hi", status_code=201)
async def ingest_hi(request: Request):
    try:
        p = hi2hi3.parse(await request.body())
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    n = msisdn.normalisasi(p["target"])
    with db.koneksi() as conn:
        row = conn.execute("SELECT id FROM target WHERE msisdn=? AND aktif=1", (n.e164,)).fetchone()
    if not row:
        raise HTTPException(404, f"{n.e164} tidak sedang disadap")
    return await _simpan(row["id"], p)


@router.get("/targets/{target_id}/berita-acara")
async def ba(target_id: str):
    try:
        return {"isi": berita_acara.buat(target_id)}
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
