from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import config


def tersedia() -> bool:
    return bool(shutil.which("tshark") and shutil.which("ffmpeg"))


def ekstrak(pcap: Path, target_id: str) -> dict:
    if not tersedia():
        raise RuntimeError("butuh tshark dan ffmpeg")
    out = config.AUDIO_DIR / target_id
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["tshark", "-r", str(pcap), "-Y", "rtp",
                        "--export-objects", f"rtp,{tmp}"],
                       check=True, capture_output=True, timeout=600)
        berkas = sorted(Path(tmp).glob("*.au")) + sorted(Path(tmp).glob("*.raw"))
        if not berkas:
            raise RuntimeError("tidak ada stream RTP")
        dst = out / f"{pcap.stem}.wav"
        if berkas[0].suffix == ".au":
            subprocess.run(["ffmpeg", "-y", "-i", str(berkas[0]), "-ar", "8000", "-ac", "1", str(dst)],
                           check=True, capture_output=True)
        else:
            shutil.copy2(berkas[0], dst)
    return {"path": dst, "kodek": "g711", "bytes": dst.stat().st_size}
