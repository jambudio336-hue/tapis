"""Adapter HI2/HI3 berbasis XML (ETSI TS 102 232)."""
from __future__ import annotations

from datetime import datetime, timezone

from lxml import etree

NS = {"x": "http://www.3gpp.org/ftp/Specs/archive/33_series/33.108"}


def parse(xml: bytes) -> dict:
    root = etree.fromstring(xml)
    jenis = "iri" if root.find(".//x:iriEvent", NS) is not None else "cc"
    target = (root.findtext(".//x:targetMSISDN", NS) or root.findtext(".//x:target", NS) or "").strip()
    corr = (root.findtext(".//x:correlationID", NS) or "").strip()
    if not target:
        raise ValueError("payload HI tidak memuat identitas target")
    return {
        "jenis": jenis,
        "target": target,
        "correlation_id": corr or target,
        "terjadi_pada": datetime.now(timezone.utc).isoformat(),
        "payload": etree.tostring(root, encoding="unicode"),
    }
