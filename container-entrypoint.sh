#!/bin/sh
set -eu

if [ "${1:-}" = '--list-interfaces' ]; then
  exec python /app/container_interfaces.py --list-interfaces
fi

if [ "$(id -u)" -ne 0 ]; then
  echo 'The container entrypoint must start as root to configure client forwarding.' >&2
  exit 1
fi

if [ "${1:-}" = '--cleanup' ]; then
  exec python /app/gateway.py --cleanup
fi

# Discovery is read-only and runs before credentials or persistent state setup.
python /app/container_interfaces.py --check-network-admin

if [ -n "${OBWEB_REO_CODE:-}" ] && [ -z "${OBWEB_USERNAME:-}" ]; then
  echo 'Set OBWEB_USERNAME when importing an OBWEB_REO_CODE.' >&2
  exit 2
fi


STATE_HOME=${XDG_STATE_HOME:-/var/lib/obweb-bridge/state}
LOGIN_STATE="$STATE_HOME/outbreak-web-login"
mkdir -p "$(dirname "${OBWEB_RUNTIME_DIR:-/var/lib/obweb-bridge/runtime}")" /run/netns
if [ -n "${OBWEB_USERNAME:-}" ]; then
  if [ -L "$STATE_HOME" ] || [ -L "$LOGIN_STATE" ]; then
    echo 'The account state path must not be a symbolic link.' >&2
    exit 1
  fi
  mkdir -p "$LOGIN_STATE"
  chown obweb:obweb "$STATE_HOME" "$LOGIN_STATE"
fi

LAN_INTERFACE=$OBWEB_LAN_INTERFACE
set -- --lan-interface "$LAN_INTERFACE"
if [ -n "${OBWEB_LAN_IP:-}" ]; then set -- "$@" --lan-ip "$OBWEB_LAN_IP"; fi
if [ -n "${OBWEB_CLIENT_IP:-}" ]; then set -- "$@" --client-ip "$OBWEB_CLIENT_IP"; fi
if [ -n "${OBWEB_WSS_URL:-}" ]; then set -- "$@" --url "$OBWEB_WSS_URL"; fi
if [ -n "${OBWEB_WSS_ORIGIN:-}" ]; then set -- "$@" --origin "$OBWEB_WSS_ORIGIN"; fi

python /app/gateway.py "$@"
runuser -u obweb -- env HOME=/home/obweb XDG_STATE_HOME="$STATE_HOME" \
  OBWEB_RUN_MODE=container \
  OBWEB_USERNAME="${OBWEB_USERNAME:-}" OBWEB_REO_CODE="${OBWEB_REO_CODE:-}" \
  python /app/login_web.py
echo 'Forwarded client IPv4 traffic will use WSS. Press Ctrl+C to stop.'
exec python /app/gateway.py "$@" --run
