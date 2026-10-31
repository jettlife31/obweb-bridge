#!/bin/sh
set -eu
BASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$(id -u)" -eq 0 ]; then
  printf 'Run as a regular user; sudo is used only for the local Ethernet endpoint.\n' >&2
  exit 1
fi
unset OBWEB_RUN_MODE OBWEB_USERNAME OBWEB_REO_CODE
if [ ! -x "$BASE_DIR/.venv/bin/python" ]; then python3 -m venv "$BASE_DIR/.venv"; fi
"$BASE_DIR/.venv/bin/python" -m pip install --quiet -r "$BASE_DIR/requirements.txt"
"$BASE_DIR/.venv/bin/python" "$BASE_DIR/app/login_web.py"
exec sudo "$BASE_DIR/.venv/bin/python" "$BASE_DIR/app/ethernet.py"
