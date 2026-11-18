from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ... import chain, db
from ...core import geoloc, msisdn, tac
from ...services.bus import bus
from ..deps import wajib_token

router = APIRouter(tags=["intel"], dependencies=[Depends(wajib_token)])


@router.get("/intel/msisdn/{nomor}")
async def intel_nomor(nomor: str):
    try:
        n = msisdn.normalisasi(nomor)
    except msisdn.NomorTidakValid as e:
        raise HTTPException(422, str(e)) from e
    return {"e164": n.e164, "nasional": n.nasional, "operator": n.operator, "mnc": n.mnc}


@router.get("/intel/imei/{imei}")
async def intel_imei(imei: str):
    r = tac.lookup(imei)
    if not r:
        raise HTTPException(422, "IMEI tidak lolos validasi Luhn")
    return r


class CellIn(BaseModel):
    mcc: str = "510"
    mnc: str
    lac: str = ""
    cid: str


@router.post("/targets/{target_id}/cell", status_code=201)
async def lapor_cell(target_id: str, body: CellIn):
    with db.connect() as conn:
        if not conn.execute("SELECT 1 FROM target WHERE id=?", (target_id,)).fetchone():
            raise HTTPException(404, "target tidak ditemukan")
    loc = await geoloc.dari_cell(body.mcc, body.mnc, body.lac, body.cid)
    if not loc:
        raise HTTPException(502, "Cell ID tidak dapat diresolusi (cek kunci API)")
    rec = {
        "mcc": body.mcc, "mnc": body.mnc, "lac": body.lac, "cid": body.cid,
        "lat": loc["lat"], "lon": loc["lon"], "akurasi": loc["akurasi"],
        "sumber": loc["sumber"], "pada": datetime.now(timezone.utc).isoformat(),
    }
    c = chain.append("cell", target_id, rec)
    with db.connect() as conn:
        cur = conn.execute(
            """INSERT INTO cell(target_id, mcc, mnc, lac, cid, lat, lon, akurasi, sumber, pada, hash, prev_hash)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (target_id, body.mcc, body.mnc, body.lac, body.cid, loc["lat"], loc["lon"],
             loc["akurasi"], loc["sumber"], rec["pada"], c["hash"], c["prev_hash"]),
        )
    out = {"id": cur.lastrowid, **rec, **c}
    await bus.pub("cell", {"target_id": target_id, "cell": out})
    return out


@router.get("/targets/{target_id}/cell")
async def riwayat_cell(target_id: str, limit: int = 500):
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM cell WHERE target_id=? ORDER BY id DESC LIMIT ?",
                            (target_id, limit)).fetchall()
    return [dict(r) for r in rows]
