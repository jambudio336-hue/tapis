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


@router.post("/targets/{target_id}/audio", status_code=201)
async def unggah(target_id: str, berkas: UploadFile = File(...), correlation_id: str = ""):
    with db.connect() as conn:
        if not conn.execute("SELECT 1 FROM target WHERE id=?", (target_id,)).fetchone():
            raise HTTPException(404, "target tidak ditemukan")
    out_dir = config.AUDIO_DIR / target_id
    out_dir.mkdir(parents=True, exist_ok=True)
    aid = str(uuid.uuid4())
    dest = out_dir / f"{aid}-{berkas.filename}"
    data = await berkas.read()
    dest.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    rec = {
        "object_key": str(dest), "sha256": sha, "bytes": len(data),
        "correlation_id": correlation_id or aid,
        "mulai": datetime.now(timezone.utc).isoformat(),
        "durasi_detik": None, "kodek": Path(berkas.filename).suffix.lstrip("."),
    }
    c = chain.append("audio", target_id, rec)
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO audio(id, target_id, correlation_id, object_key, sha256,
                   durasi_detik, kodek, mulai, bytes, hash, prev_hash)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (aid, target_id, rec["correlation_id"], rec["object_key"], sha, None,
             rec["kodek"], rec["mulai"], len(data), c["hash"], c["prev_hash"]),
        )
    out = {"id": aid, **rec, **c}
    await bus.pub("audio", {"target_id": target_id, "audio": out})
    return out


@router.post("/targets/{target_id}/audio/pcap", status_code=201)
async def dari_pcap(target_id: str, berkas: UploadFile = File(...)):
    tmp = config.AUDIO_DIR / f"tmp-{uuid.uuid4()}.pcap"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(await berkas.read())
    try:
        r = sip_rtp.ekstrak(tmp, target_id)
    except RuntimeError as e:
        raise HTTPException(422, str(e)) from e
    data = Path(r["path"]).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    aid = str(uuid.uuid4())
    rec = {"object_key": str(r["path"]), "sha256": sha, "bytes": len(data),
           "correlation_id": aid, "mulai": datetime.now(timezone.utc).isoformat(),
           "durasi_detik": None, "kodek": r["kodek"]}
    c = chain.append("audio", target_id, rec)
    with db.connect() as conn:
        conn.execute(
            """INSERT INTO audio(id, target_id, correlation_id, object_key, sha256,
                   durasi_detik, kodek, mulai, bytes, hash, prev_hash)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (aid, target_id, aid, rec["object_key"], sha, None, r["kodek"],
             rec["mulai"], len(data), c["hash"], c["prev_hash"]),
        )
    return {"id": aid, **rec, **c}


@router.get("/targets/{target_id}/audio")
async def daftar(target_id: str):
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM audio WHERE target_id=? ORDER BY id DESC", (target_id,)).fetchall()
    return [dict(r) for r in rows]


@router.get("/audio/{audio_id}/berkas")
async def ambil(audio_id: str):
    with db.connect() as conn:
        r = conn.execute("SELECT object_key FROM audio WHERE id=?", (audio_id,)).fetchone()
    if not r or not Path(r["object_key"]).exists():
        raise HTTPException(404, "audio tidak ada")
    return FileResponse(r["object_key"])


@router.get("/targets/{target_id}/manifest")
async def manifest(target_id: str):
    with db.connect() as conn:
        t = conn.execute("SELECT msisdn, imei, operator FROM target WHERE id=?", (target_id,)).fetchone()
        ev = conn.execute("SELECT id, hash, prev_hash, terjadi_pada FROM event WHERE target_id=? ORDER BY id", (target_id,)).fetchall()
        au = conn.execute("SELECT id, sha256, hash, prev_hash FROM audio WHERE target_id=? ORDER BY id", (target_id,)).fetchall()
        cl = conn.execute("SELECT id, hash, prev_hash, lat, lon FROM cell WHERE target_id=? ORDER BY id", (target_id,)).fetchall()
    return {
        "target": dict(t) if t else None,
        "chain": chain.verify(target_id),
        "event": [dict(r) for r in ev],
        "audio": [dict(r) for r in au],
        "cell": [dict(r) for r in cl],
    }
