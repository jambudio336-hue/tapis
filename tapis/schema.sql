PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS warrant (
    id                  TEXT PRIMARY KEY,
    nomor_perkara       TEXT NOT NULL,
    nomor_izin_pn       TEXT,
    legal_basis         TEXT NOT NULL,
    penyidik_nip        TEXT NOT NULL,
    instansi            TEXT NOT NULL,
    mulai               TEXT NOT NULL,
    berakhir            TEXT NOT NULL,
    ratifikasi_deadline TEXT,
    status              TEXT NOT NULL DEFAULT 'AKTIF',
    catatan             TEXT
);

CREATE TABLE IF NOT EXISTS target (
    id          TEXT PRIMARY KEY,
    warrant_id  TEXT NOT NULL REFERENCES warrant(id) ON DELETE CASCADE,
    msisdn      TEXT NOT NULL,
    operator    TEXT,
    imei        TEXT,
    tac         TEXT,
    model       TEXT,
    layanan     TEXT NOT NULL DEFAULT 'IRI_CC',
    created_at  TEXT NOT NULL,
    aktif       INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_target_msisdn ON target(msisdn);
CREATE INDEX IF NOT EXISTS idx_target_warrant ON target(warrant_id);

CREATE TABLE IF NOT EXISTS event (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id      TEXT NOT NULL REFERENCES target(id) ON DELETE CASCADE,
    correlation_id TEXT NOT NULL,
    jenis          TEXT NOT NULL,
    terjadi_pada   TEXT NOT NULL,
    diterima_pada  TEXT NOT NULL,
    payload        TEXT NOT NULL,
    hash           TEXT NOT NULL,
    prev_hash      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_event_target ON event(target_id, id);

CREATE TABLE IF NOT EXISTS cell (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id  TEXT NOT NULL REFERENCES target(id) ON DELETE CASCADE,
    mcc        TEXT NOT NULL,
    mnc        TEXT NOT NULL,
    lac        TEXT,
    cid        TEXT NOT NULL,
    lat        REAL,
    lon        REAL,
    akurasi    REAL,
    sumber     TEXT NOT NULL,
    pada       TEXT NOT NULL,
    hash       TEXT NOT NULL,
    prev_hash  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cell_target ON cell(target_id, id);

CREATE TABLE IF NOT EXISTS audio (
    id             TEXT PRIMARY KEY,
    target_id      TEXT NOT NULL REFERENCES target(id) ON DELETE CASCADE,
    correlation_id TEXT NOT NULL,
    object_key     TEXT NOT NULL,
    sha256         TEXT NOT NULL,
    durasi_detik   REAL,
    kodek          TEXT,
    mulai          TEXT NOT NULL,
    bytes          INTEGER NOT NULL,
    hash           TEXT NOT NULL,
    prev_hash      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audio_target ON audio(target_id, id);

CREATE TABLE IF NOT EXISTS chain_head (
    target_id TEXT PRIMARY KEY REFERENCES target(id) ON DELETE CASCADE,
    head      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    pada       TEXT NOT NULL,
    aktor      TEXT NOT NULL,
    aksi       TEXT NOT NULL,
    objek      TEXT,
    detail     TEXT
);

CREATE TABLE IF NOT EXISTS tac_db (
    tac   TEXT PRIMARY KEY,
    brand TEXT,
    model TEXT
);

CREATE TABLE IF NOT EXISTS operator_prefix (
    prefix   TEXT PRIMARY KEY,
    operator TEXT NOT NULL,
    mnc      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mccmnc (
    mcc      TEXT NOT NULL,
    mnc      TEXT NOT NULL,
    operator TEXT NOT NULL,
    negara   TEXT NOT NULL,
    PRIMARY KEY (mcc, mnc)
);
