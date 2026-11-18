# Arsitektur

## 1. Tujuan

LIMS yang bisa dipasang di satu mesin, jalan tanpa layanan pihak ketiga,
dan tetap memenuhi syarat pembuktian. Skala awal: satu operator lab,
puluhan target. Jalur naik ke ribuan target didokumentasikan di §9.

## 2. Zona

| Zona | Isi | Kepercayaan |
|---|---|---|
| Z1 LEA | HIC, workstation penyidik | tinggi |
| Z2 LIMS | provisioning, mediation, storage, bukti | tinggi |
| Z3 CSP | LIG/ICE, network element | menengah |
| Z4 transport | mTLS, IPsec, MPLS, NTP | kanal |

Z1–Z2 satu administrasi. Z2–Z3 dipisah mTLS. Z4 wajib NTP stratum-1.

## 3. Antarmuka

| Interface | Arah | Isi | Format |
|---|---|---|---|
| HI1 | LEA → LIMS → LIG | target, warrant, TTL, layanan | REST/JSON (TAPIS), XML/ASN.1 (ETSI) |
| HI2 | LIG → LIMS | IRI: SIP, attach, PDP, RADIUS, SMS | XML ETSI TS 102 232 |
| HI3 | LIG → LIMS | CC: RTP, payload IP, SMS body | biner |
| internal | LIMS | REST + WebSocket | JSON |

## 4. Komponen

| Komponen | Tanggung jawab |
|---|---|
| `api/routes/targets` | intake, normalisasi, warrant |
| `core/msisdn` | E.164, validasi, operator |
| `core/tac` | Luhn, TAC |
| `core/warrant` | TTL, perpanjangan, penutupan |
| `core/cellres` | resolusi sel offline + multilaterasi |
| `adapters/hi2hi3` | parse HI ETSI |
| `adapters/radius` | parse RADIUS accounting, peta CGNAT |
| `adapters/sip_rtp` | ekstraksi RTP → WAV |
| `chain` | hash chain, verifikasi, anchor |
| `services/berita_acara` | akta otomatis |
| `core/retention` | retensi, pemusnahan |

## 5. Alur data

Ingest → validasi target aktif → normalisasi → hash chain → simpan →
publish bus → WebSocket → dashboard.

Cabang geolokasi: cell masuk → resolver berlapis → koordinat + akurasi +
label sumber → hash → simpan.

Cabang audio: pcap/RTP → ekstraksi → SHA-256 → hash → simpan → putar.

## 6. Model data

`warrant` 1—N `target` 1—N (`event`, `cell`, `audio`). Setiap tabel anak
membawa `hash` dan `prev_hash`. `chain_head` menyimpan ujung rantai per
target.

Tabel referensi: `operator_prefix`, `mccmnc`, `tac_db`, `cell_db`,
`nas_map`.

## 7. Bukti

- Hash chain per target, genesis `0…0`
- Anchor harian ke berkas terpisah
- Manifest SHA-256 per berkas audio
- Berita acara memuat head dan hasil verifikasi
- Audit log append-only

`verify` menghitung ulang seluruh rantai dan menunjuk baris pertama yang
rusak.

## 8. Resolusi lokasi offline

Berlapis, berhenti di lapis pertama yang berhasil:

1. `cell_db` persis (mcc, mnc, lac, cid) → akurasi dari data
2. multilaterasi dari ≥3 sel tetangga berkoordinat → akurasi RMS
3. sel lain di `lac` sama → akurasi sedang
4. centroid operator → akurasi kasar
5. manual (`lat`/`lon` di request) → akurasi dari klien

Auto-learn: setiap laporan dengan koordinat menulis ke `cell_db`, jadi
lapis 1 makin sering kena.

## 9. Skala

| Beban | Perubahan |
|---|---|
| <50 target | SQLite, satu proses |
| <500 target | WAL, pool baca, TimescaleDB |
| <5000 target | Postgres, object store S3 Object Lock, worker terpisah |
| >5000 | shard per operator, Kafka, LIG per-CSP |

## 10. Kegagalan yang diantisipasi

| Kegagalan | Perlakuan |
|---|---|
| Jam melayang | `tapis doctor` menandai, ingest tetap jalan, berita acara menandai |
| Kunci API hilang | resolver turun ke lapis 2–4, tidak error |
| `tshark` tidak ada | upload WAV tetap jalan, capture dinonaktifkan |
| Disk penuh | ingest gagal terkontrol, hash tidak ditulis |
| Proses mati | SQLite WAL pulih, chain utuh |

## 11. Keputusan (ADR ringkas)

- **SQLite, bukan Postgres** — nol dependensi, jalan di Termux, cukup
  sampai ratusan target.
- **Hash chain, bukan tanda tangan per record** — murah, cukup untuk
  integritas; e-sign di level berita acara.
- **Resolver berlapis, bukan wajib API** — prinsip zero-key.
- **Vanilla JS, bukan React** — tanpa build step, penting di Termux.
