"""Ekstraksi audio dari capture RTP (pcap) -> WAV. Memakai tshark bila tersedia."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import config


def tersedia() -> bool:
    return shutil.which("tshark") is not None


def ekstrak(pcap: Path, target_id: str) -> dict:
    if not tersedia():
        raise RuntimeError("tshark belum terpasang (apt install tshark)")
    out_dir = config.AUDIO_DIR / target_id
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [
                "tshark", "-r", str(pcap),
                "-Y", "rtp",
                "--export-objects", f"rtp,{tmp}",
            ],
            check=True, capture_output=True, timeout=600,
        )
        files = sorted(Path(tmp).glob("*.au")) + sorted(Path(tmp).glob("*.raw"))
        if not files:
            raise RuntimeError("tidak ada stream RTP di dalam capture")
        src = files[0]
        dst = out_dir / f"{pcap.stem}.wav"
        if src.suffix == ".au":
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(src), "-ar", "8000", "-ac", "1", str(dst)],
                check=True, capture_output=True,
            )
        else:
            shutil.copy2(src, dst)
    return {"path": dst, "kodek": "g711", "bytes": dst.stat().st_size}
