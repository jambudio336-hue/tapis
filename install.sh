#!/usr/bin/env bash
set -euo pipefail

echo "== TAPIS =="

if [[ "${PREFIX:-}" == *com.termux* ]]; then
  pkg update -y
  pkg install -y python clang rust libxml2 libxslt openssl ffmpeg
  pip install --upgrade pip
  pip install -r requirements.txt
elif command -v apt >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip libxml2-dev libxslt1-dev ffmpeg
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
else
  pip install -r requirements.txt
fi

python -m tapis doctor
echo
echo "Selesai. Jalankan:"
echo "  python -m tapis up --buka"
