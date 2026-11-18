from __future__ import annotations

import shutil

from fastapi import APIRouter

from ... import __version__, config, db

router = APIRouter()


@router.get("/healthz")
async def healthz():
    with db.koneksi() as conn:
        conn.execute("SELECT 1")
    return {"ok": True, "versi": __version__,
            "tshark": bool(shutil.which("tshark")),
            "kunci_api": bool(config.OPENCELLID_KEY)}
