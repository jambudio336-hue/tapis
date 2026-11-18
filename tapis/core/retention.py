from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import config, db


def jalankan() -> dict:
    batas = (datetime.now(timezone.utc) - timedelta(days=config.RETENTION_DAYS)).isoformat()
    dihapus = 0
    with db.koneksi() as conn:
        for r in conn.execute("SELECT id,object_key FROM audio WHERE mulai < ?", (batas,)).fetchall():
            p = Path(r["object_key"])
            if p.exists():
                p.unlink()
            conn.execute("DELETE FROM audio WHERE id=?", (r["id"],))
            dihapus += 1
        conn.execute("DELETE FROM event WHERE terjadi_pada < ?", (batas,))
        conn.execute("DELETE FROM cell WHERE pada < ?", (batas,))
    return {"dihapus": dihapus, "batas": batas}
