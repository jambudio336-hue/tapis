from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ... import chain, config, db
from ...adapters import sip_rtp
from ...services.bus import bus
from ..deps import wajib_token

router = APIRouter(tags=["audio"], dependencies=[Depends(wajib_token)])


async def _catat(target_id: str, path: Path, kodek: str, data: bytes) -> dict:
    aid = str(uuid.uuid4())
    rec = {"object_key": str(path), "sha256": hashlib.sha256(data).hexdigest(),
           "bytes": len(data), "correlation_id": aid,
           "mulai": datetime.now(timezone.utc).isoformat(), "durasi_detik": None, "kodek": kodek}
    c = chain.append(target_id, rec)
    with db.koneksi() as conn:
        conn.execute(
            """INSERT INTO audio(id,target_id,correlation_id,object_key,sha256,durasi_detik,
                   kodek,mulai,bytes,hash,prev_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (aid, target_id, aid, rec["object_key"], rec["sha256"], None, kodek,
             rec["mulai"], len(data), c["hash"], c["prev_hash"]),
        )
    out = {"id": aid, **rec, **c}
    await bus.pub("audio", {"target_id": target_id, "audio": out})
    return out


@router.post("/targets/{target_id}/audio", status_code=201)
async def unggah(target_id: str, berkas: UploadFile = File(...)):
    with db.koneksi() as conn:
        if not conn.execute("SELECT 1 FROM target WHERE id=?", (target_id,)).fetchone():
            raise HTTPException(404, "target tidak ditemukan")
    out = config.AUDIO_DIR / target_id
    out.mkdir(parents=True, exist_ok=True)
    data = await berkas.read()
    dest = out / f"{uuid.uuid4()}-{berkas.filename or 'audio.wav'}"
    dest.write_bytes(data)
    return await _catat(target_id, dest, Path(dest).suffix.lstrip(".") or "wav", data)


@router.post("/targets/{target_id}/audio/pcap", status_code=201)
async def dari_pcap(target_id: str, berkas: UploadFile = File(...)):
    tmp = config.AUDIO_DIR / f"tmp-{uuid.uuid4()}.pcap"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(await berkas.read())
    try:
        r = sip_rtp.ekstrak(tmp, target_id)
    except (RuntimeError, OSError) as e:
        raise HTTPException(422, str(e)) from e
    return await _catat(target_id, Path(r["path"]), r["kodek"], Path(r["path"]).read_bytes())


@router.get("/targets/{target_id}/audio")
async def daftar(target_id: str):
    with db.koneksi() as conn:
        rows = conn.execute("SELECT * FROM audio WHERE target_id=? ORDER BY id DESC",
                            (target_id,)).fetchall()
    return [dict(r) for r in rows]


@router.get("/audio/{audio_id}/berkas")
async def ambil(audio_id: str):
    with db.koneksi() as conn:
        r = conn.execute("SELECT object_key FROM audio WHERE id=?", (audio_id,)).fetchone()
    if not r or not Path(r["object_key"]).exists():
        raise HTTPException(404, "audio tidak ada")
    return FileResponse(r["object_key"])


@router.get("/targets/{target_id}/manifest")
async def manifest(target_id: str):
    with db.koneksi() as conn:
        t = conn.execute("SELECT msisdn,imei,operator FROM target WHERE id=?", (target_id,)).fetchone()
        ev = conn.execute("SELECT id,hash,prev_hash,terjadi_pada FROM event WHERE target_id=? ORDER BY id",
                          (target_id,)).fetchall()
        au = conn.execute("SELECT id,sha256,hash,prev_hash FROM audio WHERE target_id=? ORDER BY id",
                          (target_id,)).fetchall()
        cl = conn.execute("SELECT id,hash,prev_hash,lat,lon FROM cell WHERE target_id=? ORDER BY id",
                          (target_id,)).fetchall()
    return {"target": dict(t) if t else None, "chain": chain.verify(target_id),
            "event": [dict(r) for r in ev], "audio": [dict(r) for r in au],
            "cell": [dict(r) for r in cl]}
