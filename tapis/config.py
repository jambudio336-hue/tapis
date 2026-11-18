from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _path(env: str, default: str) -> Path:
    p = Path(os.getenv(env, default)).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


TOKEN: str = os.getenv("TAPIS_TOKEN", "tapis-dev-token")
DB_PATH: Path = _path("TAPIS_DB", "./data/tapis.db")
AUDIO_DIR: Path = _path("TAPIS_AUDIO_DIR", "./data/audio")
OPENCELLID_KEY: str | None = os.getenv("OPENCELLID_KEY") or None
GOOGLE_GEOLOC_KEY: str | None = os.getenv("GOOGLE_GEOLOC_KEY") or None
RETENTION_DAYS: int = int(os.getenv("RETENTION_DAYS", "30"))
TTL_WARN_DAYS: int = int(os.getenv("TTL_WARN_DAYS", "3"))
HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8787"))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
