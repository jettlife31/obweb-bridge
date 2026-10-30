#!/bin/sh
set -eu
BASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$(id -u)" -eq 0 ]; then
  printf 'Run as a regular user; the GUI requests authorization for network setup.\n' >&2
  exit 1
fi
if [ ! -x "$BASE_DIR/.venv/bin/python" ]; then python3 -m venv "$BASE_DIR/.venv"; fi
if ! "$BASE_DIR/.venv/bin/python" -c 'import tkinter' 2>/dev/null; then
  printf 'Install Tkinter first (Debian/Ubuntu: sudo apt install python3-tk).\n' >&2
  exit 1
fi
"$BASE_DIR/.venv/bin/python" -m pip install --quiet -r "$BASE_DIR/requirements.txt"
exec "$BASE_DIR/.venv/bin/python" "$BASE_DIR/gui.py"
