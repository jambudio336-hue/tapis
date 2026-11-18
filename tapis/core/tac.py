from __future__ import annotations

import re

from .. import db

_IMEI = re.compile(r"^\d{15}$")


def luhn_ok(imei: str) -> bool:
    if not _IMEI.match(imei):
        return False
    total = 0
    for i, ch in enumerate(reversed(imei[:14])):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - total % 10) % 10 == int(imei[14])


def lookup(imei: str) -> dict | None:
    if not luhn_ok(imei):
        return None
    tac = imei[:8]
    with db.koneksi() as conn:
        row = conn.execute("SELECT brand, model FROM tac_db WHERE tac = ?", (tac,)).fetchone()
    return {"tac": tac, "brand": row["brand"] if row else None,
            "model": row["model"] if row else None, "luhn": True}
