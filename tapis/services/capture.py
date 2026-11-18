from __future__ import annotations

import hashlib
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .. import chain, config, db
from ..adapters import sip_rtp


def tersedia() -> bool:
    return sip_rtp.tersedia()


def satu_babak(iface: str, host: str, target_id: str, detik: int = 60) -> dict | None:
    with tempfile.TemporaryDirectory() as tmp:
        pcap = Path(tmp) / "babak.pcap"
        subprocess.run(["tshark", "-i", iface, "-a", f"duration:{detik}",
                        "-f", f"host {host} and udp", "-w", str(pcap), "-q"],
                       capture_output=True, timeout=detik + 30)
        if not pcap.exists() or pcap.stat().st_size < 100:
            return None
        try:
            r = sip_rtp.ekstrak(pcap, target_id)
        except (RuntimeError, subprocess.SubprocessError):
            return None

    data = Path(r["path"]).read_bytes()
    aid = str(uuid.uuid4())
    rec = {"object_key": str(r["path"]), "sha256": hashlib.sha256(data).hexdigest(),
           "bytes": len(data), "correlation_id": aid,
           "mulai": datetime.now(timezone.utc).isoformat(), "durasi_detik": None,
           "kodek": r["kodek"]}
    c = chain.append(target_id, rec)
    with db.koneksi() as conn:
        conn.execute(
            """INSERT INTO audio(id,target_id,correlation_id,object_key,sha256,durasi_detik,
                   kodek,mulai,bytes,hash,prev_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (aid, target_id, aid, rec["object_key"], rec["sha256"], None, r["kodek"],
             rec["mulai"], len(data), c["hash"], c["prev_hash"]),
        )
    return {"id": aid, **rec, **c}


def terus(iface: str, host: str, target_id: str, babak: int = 30) -> None:
    while True:
        hasil = satu_babak(iface, host, target_id, babak)
        if hasil:
            print(f"[+] audio {hasil['id']} {hasil['bytes']} byte")
