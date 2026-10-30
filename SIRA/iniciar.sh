#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then echo "Python 3 não encontrado. Instale Python 3.10 ou superior."; exit 1; fi
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python database.py
( python backend.py > backend.log 2>&1 & echo $! > backend.pid )
cleanup() { if [ -f backend.pid ]; then kill "$(cat backend.pid)" 2>/dev/null || true; rm -f backend.pid; fi; }
trap cleanup EXIT INT TERM
sleep 2
python -m streamlit run frontend.py
