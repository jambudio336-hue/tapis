from __future__ import annotations

import os
import secrets
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # tetap jalan tanpa python-dotenv
    pass

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"


def _path(env: str, default: str) -> Path:
    p = Path(os.getenv(env, default)).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _token() -> str:
    v = os.getenv("TAPIS_TOKEN", "").strip()
    if v and v != "ganti-token-ini":
        return v
    return "tapis-" + secrets.token_hex(8)


TOKEN: str = _token()
DB_PATH: Path = _path("TAPIS_DB", str(BASE / "data" / "tapis.db"))
AUDIO_DIR: Path = _path("TAPIS_AUDIO_DIR", str(BASE / "data" / "audio"))
OPENCELLID_KEY: str | None = os.getenv("OPENCELLID_KEY") or None
RETENTION_DAYS: int = int(os.getenv("RETENTION_DAYS", "30"))
TTL_WARN_DAYS: int = int(os.getenv("TTL_WARN_DAYS", "3"))
HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8787"))
