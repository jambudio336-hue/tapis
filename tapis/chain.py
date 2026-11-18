"""Hash chain append-only per target. Bukti integritas."""
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
    row = conn.execute("SELECT head FROM chain_head WHERE target_id = ?", (target_id,)).fetchone()
    return row["head"] if row else GENESIS


def append(table: str, target_id: str, payload: dict) -> dict:
    with db.connect() as conn:
        prev = head(conn, target_id)
        h = _h(payload, prev)
        conn.execute(
            "INSERT OR REPLACE INTO chain_head(target_id, head) VALUES (?,?)", (target_id, h)
        )
        return {"hash": h, "prev_hash": prev}


def anchor(target_id: str) -> dict:
    with db.connect() as conn:
        h = head(conn, target_id)
    path = config.AUDIO_DIR.parent / f"anchor-{target_id}.json"
    path.write_text(
        json.dumps(
            {"target_id": target_id, "head": h, "pada": datetime.now(timezone.utc).isoformat()},
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"head": h, "path": str(path)}


def verify(target_id: str) -> dict:
    """Hitung ulang seluruh rantai target dan bandingkan dengan head tersimpan."""
    with db.connect() as conn:
        stored = head(conn, target_id)
        prev = GENESIS
        total = 0
        for table in ("event", "cell", "audio"):
            cols = "id, hash, prev_hash, jenis" if table == "event" else "id, hash, prev_hash"
            rows = conn.execute(
                f"SELECT {cols} FROM {table} WHERE target_id = ? ORDER BY id", (target_id,)
            ).fetchall()
            for r in rows:
                total += 1
                if r["prev_hash"] != prev:
                    return {"valid": False, "rusak_di": f"{table}:{r['id']}", "diperiksa": total}
                prev = r["hash"]
    return {"valid": prev == stored, "head": stored, "dihitung": prev, "diperiksa": total}
