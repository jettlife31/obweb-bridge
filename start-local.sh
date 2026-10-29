#!/bin/sh
set -eu
BASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$(id -u)" -eq 0 ]; then
  echo 'Run as a regular user; sudo is used only for networking.' >&2
  exit 1
fi
unset OBWEB_RUN_MODE OBWEB_USERNAME OBWEB_REO_CODE OBWEB_LAN_INTERFACE OBWEB_LAN_IP
unset OBWEB_CLIENT_IP OBWEB_WSS_URL OBWEB_WSS_ORIGIN OBWEB_RUNTIME_DIR
if [ ! -x "$BASE_DIR/.venv/bin/python" ]; then python3 -m venv "$BASE_DIR/.venv"; fi
"$BASE_DIR/.venv/bin/python" -m pip install --quiet -r "$BASE_DIR/requirements.txt"
LAN_INTERFACE=$("$BASE_DIR/.venv/bin/python" "$BASE_DIR/select_interface.py")
set -- --lan-interface "$LAN_INTERFACE"
if PLAN_OUTPUT=$("$BASE_DIR/.venv/bin/python" "$BASE_DIR/gateway.py" "$@" 2>&1); then
  printf '%s\n' "$PLAN_OUTPUT"
else
  PLAN_STATUS=$?
  printf '%s\n' "$PLAN_OUTPUT" >&2
  case "$PLAN_OUTPUT" in
    *'A priority-1 policy already exists'*|*'Namespace already exists'*|*'Reserved interface already exists'*|*'Reserved nftables table already exists'*)
      if [ -d /run/outbreak-gateway ]; then
        printf 'Recorded bridge state found; attempting safe cleanup before retrying.\n' >&2
        sudo "$BASE_DIR/.venv/bin/python" "$BASE_DIR/gateway.py" --cleanup
        PLAN_OUTPUT=$("$BASE_DIR/.venv/bin/python" "$BASE_DIR/gateway.py" "$@")
        printf '%s\n' "$PLAN_OUTPUT"
      else
        exit "$PLAN_STATUS"
      fi
      ;;
    *) exit "$PLAN_STATUS" ;;
  esac
fi
TRANSIT_NETWORK=$(printf '%s\n' "$PLAN_OUTPUT" | sed -n 's/^  "transit": "\([^"]*\)",$/\1/p')
ROUTE_TABLE=$(printf '%s\n' "$PLAN_OUTPUT" | sed -n 's/^  "route_table": \([0-9][0-9]*\)$/\1/p')
if [ -z "$TRANSIT_NETWORK" ] || [ -z "$ROUTE_TABLE" ]; then
  printf 'Could not retain the selected network plan; stopping before login.\n' >&2
  exit 1
fi
set -- "$@" --transit-network "$TRANSIT_NETWORK" --route-table "$ROUTE_TABLE"
env -u OBWEB_RUN_MODE -u OBWEB_USERNAME -u OBWEB_REO_CODE \
  "$BASE_DIR/.venv/bin/python" "$BASE_DIR/login_web.py"
printf '\nAll IPv4 traffic routed from LAN clients will use WSS. Wait for READY. Press Ctrl+C to stop.\n'
exec sudo "$BASE_DIR/.venv/bin/python" "$BASE_DIR/gateway.py" "$@" --run
