# Changelog

Semua perubahan penting pada TAPIS didokumentasikan di sini.
Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.1.0/)
dan [Semantic Versioning](https://semver.org/lang/id/).

## [Unreleased]

### Planned
- Adapter GTP-C/GTP-U (S11/S1-U) untuk mobile data
- Adapter RADIUS/DHCP untuk resolusi CGNAT
- Transkripsi audio on-premise
- Multi-tenant per instansi LEA
- Ekspor berita acara ke PDF bertanda tangan TTE PSrE

## [0.1.0] - 2026-11-18

### Added
- Intake target: normalisasi E.164 +62, validasi MSISDN, deteksi operator dari prefix
- Lookup TAC/IMEI dengan validasi Luhn dan database TAC offline
- Resolusi Cell ID → koordinat via OpenCellID dan Google Geolocation (opsional)
- Warrant engine: izin PN, jalur darurat, TTL otomatis, perpanjangan, pencabutan
- Ingest IRI lewat REST dan adapter HI2/HI3 XML (ETSI TS 102 232)
- Ekstraksi audio RTP dari capture SIP/RTP (pcap) ke WAV
- Hash chain per target + anchor harian, verifikasi integritas
- Penyimpanan audio WORM-style dengan manifest SHA-256
- Dashboard web: peta Leaflet, stream event real-time via WebSocket, pemutar audio
- Generator berita acara otomatis
- Audit log append-only
- CLI dengan banner animasi menara BTS
- Installer Kali, Ubuntu, Termux
- Retensi terjadwal dan pemusnahan dengan bukti

### Security
- Token bearer + HMAC per record
- mTLS opsional untuk adapter

## [0.0.1] - 2026-10-02

### Added
- Kerangka proyek, skema database, dokumentasi arsitektur awal
