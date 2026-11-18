from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import config

SCHEMA = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")


@contextmanager
def koneksi():
    """Koneksi yang benar-benar ditutup."""
    conn = sqlite3.connect(config.DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with koneksi() as conn:
        conn.executescript(SCHEMA)


def seed() -> tuple[int, int, int]:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    pasangan = [
        ("operator_prefix_id.csv", "INSERT OR REPLACE INTO operator_prefix(prefix,operator,mnc) VALUES (?,?,?)"),
        ("tac_seed.csv", "INSERT OR REPLACE INTO tac_db(tac,brand,model) VALUES (?,?,?)"),
    ]
    n = []
    with koneksi() as conn:
        for nama, sql in pasangan:
            hitung = 0
            for baris in _baris(config.DATA_DIR / nama):
                conn.execute(sql, baris)
                hitung += 1
            n.append(hitung)
        for baris in _baris(config.DATA_DIR / "cell_seed.csv"):
            conn.execute(
                "INSERT OR IGNORE INTO cell_db(mcc,mnc,lac,cid,lat,lon,akurasi,sumber) VALUES (?,?,?,?,?,?,?,'seed')",
                baris,
            )
    return n[0], n[1], 0


def _baris(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if line.strip():
            yield tuple(c.strip() for c in line.split(","))
