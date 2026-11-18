from __future__ import annotations

from datetime import datetime, timezone

from .. import chain, db


def buat(target_id: str) -> str:
    with db.connect() as conn:
        t = conn.execute(
            """SELECT t.*, w.nomor_perkara, w.nomor_izin_pn, w.legal_basis,
                      w.penyidik_nip, w.instansi, w.mulai, w.berakhir
               FROM target t JOIN warrant w ON w.id = t.warrant_id WHERE t.id = ?""",
            (target_id,),
        ).fetchone()
        if not t:
            raise ValueError("target tidak ditemukan")
        n_ev = conn.execute("SELECT COUNT(*) c FROM event WHERE target_id=?", (target_id,)).fetchone()["c"]
        n_au = conn.execute("SELECT COUNT(*) c FROM audio WHERE target_id=?", (target_id,)).fetchone()["c"]
        n_cl = conn.execute("SELECT COUNT(*) c FROM cell WHERE target_id=?", (target_id,)).fetchone()["c"]

    v = chain.verify(target_id)
    lines = [
        "BERITA ACARA PENYADAPAN",
        "=" * 52,
        f"Dibuat      : {datetime.now(timezone.utc).isoformat()}",
        f"Nomor Perkara: {t['nomor_perkara']}",
        f"Nomor Izin PN: {t['nomor_izin_pn'] or '-'}",
        f"Dasar Hukum  : {t['legal_basis']}",
        f"Penyidik     : {t['penyidik_nip']} ({t['instansi']})",
        f"Periode      : {t['mulai']} s/d {t['berakhir']}",
        f"Target       : {t['msisdn']}",
        f"Operator     : {t['operator'] or '-'}",
        f"IMEI/TAC     : {t['imei'] or '-'} / {t['tac'] or '-'}",
        "",
        "REKAPITULASI",
        f"  Event IRI  : {n_ev}",
        f"  Objek Audio: {n_au}",
        f"  Titik Cell : {n_cl}",
        "",
        f"Chain head   : {v.get('head')}",
        f"Integritas   : {'VALID' if v['valid'] else 'RUSAK di ' + str(v.get('rusak_di'))}",
        f"Record diperiksa: {v['diperiksa']}",
    ]
    return "\n".join(lines)
