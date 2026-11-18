from __future__ import annotations

from datetime import datetime, timezone

from .. import chain, db


def buat(target_id: str) -> str:
    with db.koneksi() as conn:
        t = conn.execute(
            """SELECT t.*, w.nomor_perkara, w.nomor_izin_pn, w.legal_basis, w.penyidik_nip,
                      w.instansi, w.mulai, w.berakhir
               FROM target t JOIN warrant w ON w.id=t.warrant_id WHERE t.id=?""",
            (target_id,),
        ).fetchone()
        if not t:
            raise ValueError("target tidak ditemukan")
        n = {k: conn.execute(f"SELECT COUNT(*) c FROM {k} WHERE target_id=?",
                             (target_id,)).fetchone()["c"] for k in ("event", "audio", "cell")}
    v = chain.verify(target_id)
    return "\n".join([
        "BERITA ACARA PENYADAPAN", "=" * 52,
        f"Dibuat        : {datetime.now(timezone.utc).isoformat()}",
        f"Nomor Perkara : {t['nomor_perkara']}",
        f"Nomor Izin PN : {t['nomor_izin_pn'] or '-'}",
        f"Dasar Hukum   : {t['legal_basis']}",
        f"Penyidik      : {t['penyidik_nip']} ({t['instansi']})",
        f"Periode       : {t['mulai']} s/d {t['berakhir']}",
        f"Target        : {t['msisdn']}",
        f"Operator      : {t['operator'] or '-'}",
        f"IMEI/TAC      : {t['imei'] or '-'} / {t['tac'] or '-'}",
        "", "REKAPITULASI",
        f"  Event IRI   : {n['event']}", f"  Objek Audio : {n['audio']}",
        f"  Titik Cell  : {n['cell']}", "",
        f"Chain head    : {v.get('head')}",
        f"Integritas    : {'VALID' if v['valid'] else 'RUSAK di ' + str(v.get('rusak_di'))}",
        f"Diperiksa     : {v['diperiksa']}",
    ])
