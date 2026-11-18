from __future__ import annotations

import asyncio
import json
import sys

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
    n_op, n_tac = db.seed()
    c.print(f"[grey70]database siap[/] · prefix={n_op} tac={n_tac}")


@app.command()
def serve(host: str = config.HOST, port: int = config.PORT):
    """Jalankan API + dashboard."""
    import uvicorn

    banner.ringkas(c)
    c.print(f"[grey37]http://{host}:{port}[/]")
    uvicorn.run("tapis.api.app:app", host=host, port=port, log_level="info")


@app.command()
def intel(nomor: str):
    """Intelijen nomor: operator & normalisasi."""
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
        c.print("[red]IMEI gagal validasi Luhn")
        raise typer.Exit(1)
    c.print_json(json.dumps(r))


@app.command()
def target(nomor: str, perkara: str = "LP/001/XI/2026", basis: str = "ITE_PP71",
           penyidik: str = "000000", instansi: str = "POLRI"):
    """Daftarkan target penyadapan baru."""
    n = msisdn.normalisasi(nomor)
    wid = wr.buat(nomor_perkara=perkara, legal_basis=basis,
                  penyidik_nip=penyidik, instansi=instansi)
    import uuid
    from datetime import datetime, timezone
    tid = str(uuid.uuid4())
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO target(id, warrant_id, msisdn, operator, created_at) VALUES (?,?,?,?,?)",
            (tid, wid, n.e164, n.operator, datetime.now(timezone.utc).isoformat()),
        )
    c.print(f"[grey70]target[/] {n.e164} [grey37]({n.operator})[/] [grey37]{tid}[/]")


@app.command()
def daftar():
    """Tampilkan target aktif."""
    with db.connect() as conn:
        rows = conn.execute("SELECT id, msisdn, operator, imei, aktif FROM target").fetchall()
    t = Table("id", "msisdn", "operator", "imei", "aktif")
    for r in rows:
        t.add_row(*[str(v) for v in tuple(r)])
    c.print(t)


@app.command()
def ttl():
    """Tutup warrant kedaluwarsa, tampilkan yang hampir habis."""
    c.print_json(json.dumps({"ditutup": wr.kedaluwarsa(), "hampir": wr.hampir_habis()}))


@app.command()
def verify(target_id: str):
    """Verifikasi integritas rantai bukti."""
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
    """Resolusi Cell ID -> koordinat."""
    r = asyncio.run(geoloc.dari_cell("510", mnc, lac, cid))
    c.print_json(json.dumps(r or {"hasil": None}))


@app.command()
def bersihkan():
    """Jalankan retensi."""
    c.print_json(json.dumps(retensi()))


@app.command()
def doctor():
    """Cek kesiapan lingkungan."""
    import shutil
    ok = {
        "python": sys.version.split()[0],
        "sqlite": True,
        "tshark": bool(shutil.which("tshark")),
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "token_default": config.TOKEN == "tapis-dev-token",
        "opencellid": bool(config.OPENCELLID_KEY),
    }
    c.print_json(json.dumps(ok))


def main():
    app()


if __name__ == "__main__":
    main()
