"""Resolusi Cell ID -> koordinat. Sumber nyata, butuh kunci API."""
from __future__ import annotations

import math

import httpx

from .. import config

OPENCELLID = "https://opencellid.org/cell/get"
GOOGLE = "https://www.googleapis.com/geolocation/v1/geolocate"


async def dari_cell(mcc: str, mnc: str, lac: str, cid: str) -> dict | None:
    if config.OPENCELLID_KEY:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(
                    OPENCELLID,
                    params={
                        "key": config.OPENCELLID_KEY,
                        "mcc": mcc,
                        "mnc": mnc,
                        "lac": lac,
                        "cellid": cid,
                        "format": "json",
                    },
                )
                if r.status_code == 200:
                    d = r.json()
                    if "lat" in d:
                        return {
                            "lat": d["lat"],
                            "lon": d["lon"],
                            "akurasi": d.get("range", 0) or 0,
                            "sumber": "opencellid",
                        }
        except (httpx.HTTPError, ValueError):
            pass
    if config.GOOGLE_GEOLOC_KEY:
        body = {
            "cellTowers": [
                {
                    "cellId": int(cid),
                    "locationAreaCode": int(lac or 0),
                    "mobileCountryCode": int(mcc),
                    "mobileNetworkCode": int(mnc),
                }
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post(GOOGLE, params={"key": config.GOOGLE_GEOLOC_KEY}, json=body)
                if r.status_code == 200:
                    d = r.json()
                    loc = d.get("location", {})
                    return {
                        "lat": loc.get("lat"),
                        "lon": loc.get("lng"),
                        "akurasi": d.get("accuracy", 0) or 0,
                        "sumber": "google",
                    }
        except (httpx.HTTPError, ValueError):
            pass
    return None


def jarak_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6_371_000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))
