#!/usr/bin/env bash
set -euo pipefail

echo "== TAPIS installer =="

if [[ "${PREFIX:-}" == *com.termux* ]]; then
  echo "[i] Termux terdeteksi"
  pkg update -y
  pkg install -y python clang libxml2 libxslt openssl tshark ffmpeg
  PY=python
  pip install --upgrade pip
  pip install -r requirements.txt
elif command -v apt >/dev/null 2>&1; then
  echo "[i] Debian/Ubuntu terdeteksi"
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip libxml2-dev libxslt1-dev \
    tshark ffmpeg
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "[!] distro tidak dikenali, lanjut dengan pip saja"
  pip install -r requirements.txt
fi

cp -n .env.example .env || true
python -m tapis init
echo
echo "Selesai. Jalankan:  source .venv/bin/activate 2>/dev/null; tapis serve"
