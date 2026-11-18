from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ... import db
from ...adapters import radius
from ...core import msisdn
from ..deps import wajib_token

router = APIRouter(prefix="/radius", tags=["radius"], dependencies=[Depends(wajib_token)])


@router.post("/accounting", status_code=201)
async def terima(request: Request):
    try:
        sesi = radius.parse(await request.body())
    except radius.RadiusRusak as e:
        raise HTTPException(422, str(e)) from e
    nomor = sesi.calling_station_id
    if nomor:
        try:
            nomor = msisdn.normalisasi(nomor).e164
        except msisdn.NomorTidakValid:
            pass
    with db.koneksi() as conn:
        cur = conn.execute(
            """INSERT INTO radius_session(user_name,calling_station_id,framed_ip,nas_port,
                   nas_port_id,nas_ip,acct_status,acct_session_id,pada) VALUES (?,?,?,?,?,?,?,?,?)""",
            (sesi.user_name, nomor, sesi.framed_ip, sesi.nas_port, sesi.nas_port_id,
             sesi.nas_ip, sesi.acct_status, sesi.acct_session_id, sesi.pada),
        )
    return {"id": cur.lastrowid, "nomor": nomor, "publik": sesi.publik(),
            "status": sesi.acct_status}


@router.get("/cari/{nomor}")
async def cari(nomor: str):
    try:
        n = msisdn.normalisasi(nomor).e164
    except msisdn.NomorTidakValid as e:
        raise HTTPException(422, str(e)) from e
    with db.koneksi() as conn:
        rows = conn.execute(
            """SELECT * FROM radius_session WHERE calling_station_id=? AND status_aktif
               ORDER BY id DESC""".replace("status_aktif", "acct_status != 'stop'"),
            (n,),
        ).fetchall()
    return [dict(r) for r in rows]
