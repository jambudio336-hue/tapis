"""Resolusi lokasi offline berlapis. Tanpa kunci API."""
from __future__ import annotations

import math

from .. import db

AKURASI_CENTROID = 400_000.0


def jarak_m(a, b) -> float:
    r = 6_371_000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    h = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(h))


def _persis(mcc, mnc, lac, cid):
    with db.koneksi() as conn:
        r = conn.execute(
            "SELECT lat, lon, akurasi FROM cell_db WHERE mcc=? AND mnc=? AND lac=? AND cid=?",
            (mcc, mnc, lac, cid),
        ).fetchone()
    return {"lat": r["lat"], "lon": r["lon"], "akurasi": r["akurasi"],
            "sumber": "sel-diketahui"} if r else None


def trilaterasi(titik):
    if len(titik) < 3:
        return None
    x0, y0, r0 = titik[0]
    A, b = [], []
    for x, y, r in titik[1:]:
        A.append([2 * (x - x0), 2 * (y - y0)])
        b.append((x * x - x0 * x0) + (y * y - y0 * y0) - (r * r - r0 * r0))
    a11 = sum(p[0] ** 2 for p in A)
    a12 = sum(p[0] * p[1] for p in A)
    a22 = sum(p[1] ** 2 for p in A)
    b1 = sum(p[0] * v for p, v in zip(A, b))
    b2 = sum(p[1] * v for p, v in zip(A, b))
    det = a11 * a22 - a12 * a12
    if abs(det) < 1e-12:
        return None
    x = (b1 * a22 - b2 * a12) / det
    y = (a11 * b2 - a12 * b1) / det
    resid = [jarak_m((x, y), (px, py)) - pr for px, py, pr in titik]
    rms = math.sqrt(sum(v * v for v in resid) / len(resid))
    return {"lat": x, "lon": y, "akurasi": max(rms, 50.0), "sumber": "multilaterasi"}


def _tetangga(mcc, mnc, lac, limit=8):
    with db.koneksi() as conn:
        rows = conn.execute(
            """SELECT lat, lon, akurasi FROM cell_db
               WHERE mcc=? AND mnc=? AND lac=? AND lat IS NOT NULL LIMIT ?""",
            (mcc, mnc, lac, limit),
        ).fetchall()
    return [(r["lat"], r["lon"], r["akurasi"] or 500.0) for r in rows]


def _centroid(mnc):
    with db.koneksi() as conn:
        r = conn.execute("SELECT AVG(lat) la, AVG(lon) lo FROM cell_db WHERE mnc=?",
                         (mnc,)).fetchone()
    if not r or r["la"] is None:
        return None
    return {"lat": r["la"], "lon": r["lo"], "akurasi": AKURASI_CENTROID, "sumber": "centroid"}


def resolve(mcc, mnc, lac, cid):
    return _persis(mcc, mnc, lac, cid) or trilaterasi(_tetangga(mcc, mnc, lac)) or _centroid(mnc)


def belajar(mcc, mnc, lac, cid, lat, lon, akurasi) -> None:
    with db.koneksi() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO cell_db(mcc,mnc,lac,cid,lat,lon,akurasi,sumber)
               VALUES (?,?,?,?,?,?,?,'auto')""",
            (mcc, mnc, lac, cid, lat, lon, akurasi),
        )
