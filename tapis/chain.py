from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from . import config, db

GENESIS = "0" * 64


def _h(payload: dict, prev: str) -> str:
    blob = prev.encode() + json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def head(conn, target_id: str) -> str:
    r = conn.execute("SELECT head FROM chain_head WHERE target_id=?", (target_id,)).fetchone()
    return r["head"] if r else GENESIS


def append(target_id: str, payload: dict) -> dict:
    with db.koneksi() as conn:
        prev = head(conn, target_id)
        h = _h(payload, prev)
        conn.execute("INSERT OR REPLACE INTO chain_head(target_id,head) VALUES (?,?)",
                     (target_id, h))
    return {"hash": h, "prev_hash": prev}


def verify(target_id: str) -> dict:
    with db.koneksi() as conn:
        stored = head(conn, target_id)
        prev = GENESIS
        total = 0
        for tabel in ("event", "cell", "audio"):
            for r in conn.execute(
                f"SELECT id,hash,prev_hash FROM {tabel} WHERE target_id=? ORDER BY id",
                (target_id,),
            ).fetchall():
                total += 1
                if r["prev_hash"] != prev:
                    return {"valid": False, "rusak_di": f"{tabel}:{r['id']}", "diperiksa": total}
                prev = r["hash"]
    return {"valid": prev == stored, "head": stored, "dihitung": prev, "diperiksa": total}


def anchor(target_id: str) -> dict:
    with db.koneksi() as conn:
        h = head(conn, target_id)
    p = config.DATA_DIR / f"anchor-{target_id}.json"
    p.write_text(json.dumps({"target_id": target_id, "head": h,
                             "pada": datetime.now(timezone.utc).isoformat()}, indent=2))
    return {"head": h, "path": str(p)}
