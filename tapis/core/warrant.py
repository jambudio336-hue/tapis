from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from .. import config, db

BASIS = {"ITE_PP71": 30, "TERORISME": 30, "NARKOTIKA": 30, "TIPIKOR": 30, "KPK": 30, "DARURAT": 1}


def buat(*, nomor_perkara, legal_basis, penyidik_nip, instansi,
         hari=None, nomor_izin_pn=None, darurat=False) -> str:
    if legal_basis not in BASIS:
        raise ValueError(f"legal_basis tidak dikenal: {legal_basis}")
    now = datetime.now(timezone.utc)
    wid = str(uuid.uuid4())
    with db.koneksi() as conn:
        conn.execute(
            """INSERT INTO warrant(id,nomor_perkara,nomor_izin_pn,legal_basis,penyidik_nip,
                   instansi,mulai,berakhir,ratifikasi_deadline)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (wid, nomor_perkara, nomor_izin_pn, legal_basis, penyidik_nip, instansi,
             now.isoformat(), (now + timedelta(days=hari or BASIS[legal_basis])).isoformat(),
             (now + timedelta(hours=24)).isoformat() if darurat else None),
        )
    return wid


def kedaluwarsa() -> list[str]:
    now = datetime.now(timezone.utc).isoformat()
    with db.koneksi() as conn:
        rows = conn.execute("SELECT id FROM warrant WHERE status='AKTIF' AND berakhir <= ?",
                            (now,)).fetchall()
        for r in rows:
            conn.execute("UPDATE warrant SET status='SELESAI' WHERE id=?", (r["id"],))
            conn.execute("UPDATE target SET aktif=0 WHERE warrant_id=?", (r["id"],))
    return [r["id"] for r in rows]


def hampir_habis() -> list[dict]:
    batas = (datetime.now(timezone.utc) + timedelta(days=config.TTL_WARN_DAYS)).isoformat()
    with db.koneksi() as conn:
        rows = conn.execute(
            "SELECT id,nomor_perkara,berakhir FROM warrant WHERE status='AKTIF' AND berakhir <= ?",
            (batas,)).fetchall()
    return [dict(r) for r in rows]
