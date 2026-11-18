from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ... import db
from ...core import msisdn, tac, warrant as wr
from ..deps import wajib_token

router = APIRouter(prefix="/targets", tags=["targets"], dependencies=[Depends(wajib_token)])


class BuatTarget(BaseModel):
    msisdn: str = Field(examples=["+6281234567890"])
    imei: str | None = None
    nomor_perkara: str = "LP/001/XI/2026"
    legal_basis: str = "ITE_PP71"
    penyidik_nip: str = "000000"
    instansi: str = "POLRI"
    nomor_izin_pn: str | None = None
    darurat: bool = False


@router.post("", status_code=201)
async def buat(body: BuatTarget):
    try:
        n = msisdn.normalisasi(body.msisdn)
    except msisdn.NomorTidakValid as e:
        raise HTTPException(422, str(e)) from e
    t = tac.lookup(body.imei) if body.imei else None
    wid = wr.buat(nomor_perkara=body.nomor_perkara, legal_basis=body.legal_basis,
                  penyidik_nip=body.penyidik_nip, instansi=body.instansi,
                  nomor_izin_pn=body.nomor_izin_pn, darurat=body.darurat)
    tid = str(uuid.uuid4())
    with db.koneksi() as conn:
        conn.execute(
            """INSERT INTO target(id,warrant_id,msisdn,operator,imei,tac,model,created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (tid, wid, n.e164, n.operator, body.imei if t else None,
             t["tac"] if t else None,
             f"{t['brand']} {t['model']}" if t and t.get("brand") else None,
             datetime.now(timezone.utc).isoformat()),
        )
        conn.execute("INSERT INTO audit(pada,aktor,aksi,objek,detail) VALUES (?,?,?,?,?)",
                     (datetime.now(timezone.utc).isoformat(), body.penyidik_nip,
                      "TARGET_DIBUAT", tid, n.e164))
    return {"id": tid, "warrant_id": wid, "msisdn": n.e164, "operator": n.operator,
            "imei_valid": bool(t), "perangkat": t}


@router.get("")
async def daftar(aktif: bool = True):
    with db.koneksi() as conn:
        rows = conn.execute("SELECT * FROM target WHERE aktif=? ORDER BY created_at DESC",
                            (1 if aktif else 0,)).fetchall()
    return [dict(r) for r in rows]


@router.get("/{target_id}")
async def detail(target_id: str):
    with db.koneksi() as conn:
        r = conn.execute("SELECT * FROM target WHERE id=?", (target_id,)).fetchone()
        if not r:
            raise HTTPException(404, "target tidak ditemukan")
        w = conn.execute("SELECT * FROM warrant WHERE id=?", (r["warrant_id"],)).fetchone()
    return {"target": dict(r), "warrant": dict(w)}
