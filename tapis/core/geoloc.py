from __future__ import annotations

import json
import urllib.parse
import urllib.request

from .. import config
from . import cellres

URL = "https://opencellid.org/cell/get"


def dari_cell(mcc: str, mnc: str, lac: str, cid: str) -> dict | None:
    lokal = cellres.resolve(mcc, mnc, lac, cid)
    if lokal and lokal["sumber"] != "centroid":
        return lokal
    if config.OPENCELLID_KEY:
        q = urllib.parse.urlencode({"key": config.OPENCELLID_KEY, "mcc": mcc, "mnc": mnc,
                                    "lac": lac, "cellid": cid, "format": "json"})
        try:
            with urllib.request.urlopen(f"{URL}?{q}", timeout=8) as r:
                d = json.loads(r.read().decode())
            if "lat" in d:
                hasil = {"lat": d["lat"], "lon": d["lon"],
                         "akurasi": float(d.get("range") or 0), "sumber": "opencellid"}
                cellres.belajar(mcc, mnc, lac, cid, hasil["lat"], hasil["lon"], hasil["akurasi"])
                return hasil
        except (OSError, ValueError):
            pass
    return lokal
