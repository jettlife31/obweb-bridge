#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo 'The container entrypoint must start as root to configure client forwarding.' >&2
  exit 1
fi

if [ "${1:-}" = '--cleanup' ]; then
  exec python /app/gateway.py --cleanup
fi

STATE_HOME=${XDG_STATE_HOME:-/var/lib/obweb-bridge/state}
LOGIN_STATE="$STATE_HOME/outbreak-web-login"
if [ -L "$STATE_HOME" ] || [ -L "$LOGIN_STATE" ]; then
  echo 'The account state path must not be a symbolic link.' >&2
  exit 1
fi
mkdir -p "$LOGIN_STATE" "$(dirname "${OBWEB_RUNTIME_DIR:-/var/lib/obweb-bridge/runtime}")" /run/netns
chown obweb:obweb "$STATE_HOME" "$LOGIN_STATE"

if [ -n "${OBWEB_LAN_INTERFACE:-}" ]; then
  LAN_INTERFACE=$OBWEB_LAN_INTERFACE
else
  LAN_INTERFACE=$(python /app/select_interface.py)
fi

python /app/gateway.py --lan-interface "$LAN_INTERFACE"
runuser -u obweb -- env HOME=/home/obweb XDG_STATE_HOME="$STATE_HOME" python /app/login_web.py
echo 'Forwarded client IPv4 traffic will use WSS. Press Ctrl+C to stop.'
exec python /app/gateway.py --lan-interface "$LAN_INTERFACE" --run
