from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config

SCHEMA = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def seed() -> tuple[int, int]:
    """Muat data referensi operator & TAC. Idempotent."""
    op = config.DATA_DIR / "operator_prefix_id.csv"
    tac = config.DATA_DIR / "tac_seed.csv"
    n_op = n_tac = 0
    with connect() as conn:
        for row in _rows(op):
            conn.execute(
                "INSERT OR REPLACE INTO operator_prefix(prefix, operator, mnc) VALUES (?,?,?)",
                row,
            )
            n_op += 1
        for row in _rows(tac):
            conn.execute(
                "INSERT OR REPLACE INTO tac_db(tac, brand, model) VALUES (?,?,?)", row
            )
            n_tac += 1
    return n_op, n_tac


def _rows(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if line.strip():
            yield tuple(c.strip() for c in line.split(","))
