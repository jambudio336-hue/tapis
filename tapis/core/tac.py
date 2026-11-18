"""Validasi IMEI (Luhn) dan lookup TAC."""
from __future__ import annotations

import re

from .. import db

_IMEI = re.compile(r"^\d{14,15}$")


def luhn_ok(imei: str) -> bool:
    if not _IMEI.match(imei):
        return False
    digit = imei[:14]
    total = 0
    for i, ch in enumerate(reversed(digit)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - total % 10) % 10 == int(imei[14] if len(imei) == 15 else 0)


def lookup(imei: str) -> dict | None:
    if not luhn_ok(imei):
        return None
    tac = imei[:8]
    with db.connect() as conn:
        row = conn.execute("SELECT brand, model FROM tac_db WHERE tac = ?", (tac,)).fetchone()
    if not row:
        return {"tac": tac, "brand": None, "model": None}
    return {"tac": tac, "brand": row["brand"], "model": row["model"]}
