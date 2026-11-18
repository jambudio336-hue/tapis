from __future__ import annotations

from datetime import datetime, timezone
from xml.etree import ElementTree as ET

IRI = ("iriEvent", "iri", "event")


def parse(xml: bytes) -> dict:
    root = ET.fromstring(xml)
    tag = root.tag.split("}")[-1].lower()
    target = corr = ""
    for el in root.iter():
        nama = el.tag.split("}")[-1].lower()
        if nama in ("targetmsisdn", "target", "msisdn") and el.text:
            target = el.text.strip()
        if nama == "correlationid" and el.text:
            corr = el.text.strip()
    if not target:
        raise ValueError("payload HI tanpa identitas target")
    return {
        "jenis": "IRI" if tag in IRI else "CC",
        "target": target,
        "correlation_id": corr or target,
        "terjadi_pada": datetime.now(timezone.utc).isoformat(),
        "payload": ET.tostring(root, encoding="unicode"),
    }
