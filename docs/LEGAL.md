# Dasar Hukum & Pemetaan Kepatuhan

> Dokumen kerja, bukan nasihat hukum. Verifikasi nomor pasal dengan
> bagian hukum instansi lo sebelum dipakai di berkas perkara.

## 1. Prinsip

TAPIS tidak menciptakan kewenangan. Kewenangan datang dari penyidik dan
izin pengadilan. TAPIS hanya memastikan setiap kewenangan itu
**tercatat, terbatas waktu, dan tidak bisa diubah belakangan**.

Konsekuensi desain: tidak ada satu rezim hukum yang di-hardcode. Setiap
warrant membawa `legal_basis`, dan basis itu menentukan durasi, jalur
persetujuan, dan artefak audit yang wajib dihasilkan.

## 2. Peta dasar hukum

### 2.1 Intersepsi oleh penegak hukum

| Instrumen | Isi pokok |
|---|---|
| Pasal 31 UU 11/2008 jo. UU 19/2016 (ITE) | Intersepsi/penyadapan atas informasi elektronik; dilakukan atas permintaan penegak hukum; tata cara didelegasikan ke PP |
| Pasal 31 ayat (4) UU ITE | Perintah delegasi → PP 71/2019 |
| PP 71/2019 | Prosedur: permohonan izin Ketua PN, batas waktu, perpanjangan, kewajiban penyimpanan oleh penyelenggara, berita acara, penyerahan hasil |
| Pasal 42 UU 36/1999 | Kerahasiaan informasi pelanggan |
| Pasal 43 UU 36/1999 | Penyelenggara telekomunikasi dapat melakukan penyadapan untuk kepentingan penyelidikan |

### 2.2 Rezim sektoral

| Instrumen | Cakupan | Catatan |
|---|---|---|
| UU 5/2018 (Terorisme) | Penyadapan oleh aparat dalam pemberantasan terorisme | Wewenang lebih luas, koordinasi BNPT |
| UU 19/2019 (KPK) | Penyadapan oleh KPK | Ada mekanisme persetujuan Dewas untuk tindakan tertentu |
| UU 35/2009 Pasal 75–77 (Narkotika) | Penyadapan oleh BNN/Polri | Terkait penyadapan dan penyadapan telekomunikasi |
| UU Tipikor | Penyadapan dalam penyidikan korupsi | — |

### 2.3 Perlindungan data

| Instrumen | Konsekuensi teknis |
|---|---|
| UU 27/2022 (PDP) | Dasar pemrosesan, minimisasi, pembatasan retensi, hak subjek data |
| PP 71/2019 | Kewajiban retensi hasil oleh penyelenggara |

Konsekuensi: retensi **wajib berbatas** dan pemusnahan **wajib berbukti**.
TAPIS mencatat batas retensi per target dan menghasilkan catatan
pemusnahan.

### 2.4 Alat bukti

| Instrumen | Konsekuensi teknis |
|---|---|
| Pasal 5 UU ITE | Dokumen elektronik sah sebagai alat bukti bila sistemnya terjamin integritasnya |
| Pasal 6 UU ITE | Penandatanganan elektronik butuh TTE tersertifikasi |
| Pasal 44 UU ITE | Alat bukti elektronik dalam pemeriksaan |

Konsekuensi: **hash chain, timestamp, dan e-sign bukan fitur tambahan,
tapi syarat sahnya bukti.** Tanpa itu, hasil sadapan hanya "rekaman",
bukan alat bukti.

## 3. Matriks fitur → pasal → artefak audit

| Fitur TAPIS | Dasar | Artefak |
|---|---|---|
| `nomor_izin_pn` wajib pada basis non-darurat | PP 71/2019 | kolom warrant |
| Jalur darurat + `ratifikasi_deadline` 24 jam | PP 71/2019 | kolom warrant |
| TTL otomatis + peringatan H-3 | batas waktu PP 71/2019 | audit log + status |
| Hash chain per target | Pasal 5 UU ITE | tabel chain_head |
| Timestamp ISO-8601 UTC | Pasal 5 UU ITE | kolom `terjadi_pada` |
| Manifest SHA-256 | Pasal 5 UU ITE | endpoint manifest |
| Berita acara | PP 71/2019 | endpoint berita-acara |
| Retensi + pemusnahan | UU 27/2022 | `tapis bersihkan` |
| Audit log append-only | akuntabilitas | tabel audit |

## 4. Yang membuat hasil sadapan gugur

1. **Izin habis, intersepsi jalan terus.** Pembela menyerang otomatis.
   Mitigasi: TTL engine, auto-tutup, peringatan H-3.
2. **Jam tidak sinkron.** Urutan event jadi tidak bisa
   dipertanggungjawabkan. Mitigasi: NTP wajib di semua titik.
3. **Tidak ada hash.** Tidak bisa membuktikan berkas tidak diedit.
   Mitigasi: hash chain + anchor.
4. **Target tidak jelas.** Salah nomor, salah IMSI. Mitigasi: normalisasi
   E.164 dan pencatatan identitas target di berita acara.
5. **Tidak ada berita acara.** Tidak ada jejak serah terima.
   Mitigasi: generator otomatis.
6. **Retensi tak terkendali.** Melanggar PDP. Mitigasi: retensi terjadwal.

## 5. Checklist per perkara

- [ ] Surat permohonan penyidik ada
- [ ] Nomor izin Ketua PN tercatat (atau jalur darurat + ratifikasi ≤24 jam)
- [ ] `legal_basis` benar
- [ ] Target dinormalisasi dan dikonfirmasi ke penyidik
- [ ] TTL sesuai izin, bukan default
- [ ] NTP sinkron (`timedatectl` / `chronyc tracking`)
- [ ] `tapis verify` bersih sebelum penyerahan
- [ ] Berita acara dicetak dan ditandatangani
- [ ] Retensi diset
- [ ] Pemusnahan terjadwal setelah perkara inkracht

## 6. Catatan yurisdiksi

TAPIS dirancang untuk Indonesia (MCC 510). Untuk penggunaan lintas
negara, `legal_basis` dan durasi harus disesuaikan.
