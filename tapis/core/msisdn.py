from __future__ import annotations

import re
from dataclasses import dataclass

from .. import db

_STRIP = re.compile(r"[^\d+]")


class NomorTidakValid(ValueError):
    pass


@dataclass(frozen=True)
class Nomor:
    e164: str
    nasional: str
    operator: str | None
    mnc: str | None


def bersihkan(raw: str) -> str:
    s = _STRIP.sub("", raw.strip())
    if s.startswith("00"):
        s = "+" + s[2:]
    if s.startswith("62"):
        s = "+" + s
    elif s.startswith("0"):
        s = "+62" + s[1:]
    elif s.startswith("8"):
        s = "+62" + s
    if not s.startswith("+62"):
        raise NomorTidakValid(f"bukan nomor Indonesia: {raw}")
    return s


def normalisasi(raw: str) -> Nomor:
    e164 = bersihkan(raw)
    digit = e164[1:]
    if not (10 <= len(digit) <= 14) or not digit.isdigit():
        raise NomorTidakValid(f"format tidak wajar: {raw}")
    nasional = "0" + digit[2:]
    with db.koneksi() as conn:
        row = conn.execute(
            "SELECT operator, mnc FROM operator_prefix WHERE prefix = ?", (nasional[:4],)
        ).fetchone()
    return Nomor(e164, nasional, row["operator"] if row else None, row["mnc"] if row else None)


def ke_nasional(e164: str) -> str:
    return "0" + e164[3:]
