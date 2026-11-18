from __future__ import annotations

import json
import os
import secrets
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import __version__, banner, config, db
from .core import geoloc, msisdn, tac, warrant as wr
from .core.retention import jalankan as retensi
from .services import berita_acara

app = typer.Typer(add_completion=False, help="TAPIS — LIMS untuk Indonesia")
c = Console()


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context, versi: bool = typer.Option(False, "--version", "-v")):
    if versi:
        c.print(f"tapis {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        banner.tampilkan(c)


@app.command()
def init():
    """Siapkan database dan data referensi."""
    db.init_db()
    op, tc, _ = db.seed()
    c.print(f"[grey70]siap[/] prefix={op} tac={tc}")


@app.command()
def up(host: str = config.HOST, port: int = config.PORT, buka: bool = False):
    """Siapkan semua lalu jalankan server. Satu perintah."""
    env = Path(".env")
    token = secrets.token_urlsafe(24)
    env.write_text(
        f"TAPIS_TOKEN={token}\nRETENTION_DAYS=30\nTTL_WARN_DAYS=3\nHOST={host}\nPORT={port}\n"
    )
    os.environ["TAPIS_TOKEN"] = token
    config.TOKEN = token
    db.init_db()
    db.seed()
    url = f"http://{host}:{port}/?t={token}"
    c.print(f"[bold]token[/] {token}")
    c.print(f"[bold]buka [/] {url}")
    if buka:
        import webbrowser
        webbrowser.open(url)
    import uvicorn
    uvicorn.run("tapis.api.app:app", host=host, port=port)


@app.command()
def serve(host: str = config.HOST, port: int = config.PORT):
    """Jalankan server memakai .env yang ada."""
    import uvicorn
    banner.ringkas(c)
    c.print(f"[grey37]http://{host}:{port}/?t={config.TOKEN}[/]")
    uvicorn.run("tapis.api.app:app", host=host, port=port)


@app.command()
def intel(nomor: str):
    """Intelijen nomor."""
    try:
        n = msisdn.normalisasi(nomor)
    except msisdn.NomorTidakValid as e:
        c.print(f"[red]{e}")
        raise typer.Exit(1)
    c.print_json(json.dumps({"e164": n.e164, "operator": n.operator, "mnc": n.mnc}))


@app.command()
def imei(kode: str):
    """Lookup TAC dari IMEI."""
    r = tac.lookup(kode)
    if not r:
        c.print("[red]IMEI gagal Luhn")
        raise typer.Exit(1)
    c.print_json(json.dumps(r))


@app.command()
def target(nomor: str, perkara: str = "LP/001/XI/2026", basis: str = "ITE_PP71",
           penyidik: str = "000000", instansi: str = "POLRI"):
    """Daftarkan target."""
    n = msisdn.normalisasi(nomor)
    wid = wr.buat(nomor_perkara=perkara, legal_basis=basis, penyidik_nip=penyidik, instansi=instansi)
    tid = str(uuid.uuid4())
    with db.koneksi() as conn:
        conn.execute("INSERT INTO target(id,warrant_id,msisdn,operator,created_at) VALUES (?,?,?,?,?)",
                     (tid, wid, n.e164, n.operator, datetime.now(timezone.utc).isoformat()))
    c.print(f"[grey70]target[/] {n.e164} [grey37]{tid}[/]")


@app.command()
def daftar():
    """Target aktif."""
    with db.koneksi() as conn:
        rows = conn.execute("SELECT id,msisdn,operator,aktif FROM target").fetchall()
    t = Table("id", "msisdn", "operator", "aktif")
    for r in rows:
        t.add_row(*[str(v) for v in tuple(r)])
    c.print(t)


@app.command()
def ttl():
    """Tutup warrant kedaluwarsa."""
    c.print_json(json.dumps({"ditutup": wr.kedaluwarsa(), "hampir": wr.hampir_habis()}))


@app.command()
def verify(target_id: str):
    """Verifikasi rantai bukti."""
    from . import chain
    r = chain.verify(target_id)
    c.print_json(json.dumps(r))
    raise typer.Exit(0 if r["valid"] else 1)


@app.command("berita-acara")
def ba(target_id: str):
    """Cetak berita acara."""
    c.print(berita_acara.buat(target_id))


@app.command()
def cell(mnc: str, cid: str, lac: str = ""):
    """Resolusi sel."""
    c.print_json(json.dumps(geoloc.dari_cell("510", mnc, lac, cid) or {"hasil": None}))


@app.command()
def capture(iface: str, host: str, target_id: str, babak: int = 30):
    """Tangkap RTP terus-menerus."""
    from .services import capture as cap
    if not cap.tersedia():
        c.print("[red]butuh tshark dan ffmpeg")
        raise typer.Exit(1)
    cap.terus(iface, host, target_id, babak)


@app.command()
def bersihkan():
    """Jalankan retensi."""
    c.print_json(json.dumps(retensi()))


@app.command()
def doctor():
    """Cek kesiapan."""
    c.print_json(json.dumps({
        "python": sys.version.split()[0],
        "tshark": bool(shutil.which("tshark")),
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "opencellid": bool(config.OPENCELLID_KEY),
        "db": str(config.DB_PATH),
    }))


def main():
    app()
