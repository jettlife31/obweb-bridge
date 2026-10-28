#!/bin/sh
set -eu
BASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$(id -u)" -eq 0 ]; then
  echo 'Run as a regular user; sudo is used only for networking.' >&2
  exit 1
fi
if [ ! -x "$BASE_DIR/.venv/bin/python" ]; then python3 -m venv "$BASE_DIR/.venv"; fi
"$BASE_DIR/.venv/bin/python" -m pip install --quiet -r "$BASE_DIR/requirements.txt"
LAN_INTERFACE=$("$BASE_DIR/.venv/bin/python" "$BASE_DIR/select_interface.py")
set -- --lan-interface "$LAN_INTERFACE"
"$BASE_DIR/.venv/bin/python" "$BASE_DIR/gateway.py" "$@"
env -u OBWEB_USERNAME -u OBWEB_REO_CODE "$BASE_DIR/.venv/bin/python" "$BASE_DIR/login_web.py"
printf '\nAll IPv4 traffic routed from LAN clients will use WSS. Wait for READY. Press Ctrl+C to stop.\n'
exec sudo "$BASE_DIR/.venv/bin/python" "$BASE_DIR/gateway.py" "$@" --run
