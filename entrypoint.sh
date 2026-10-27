#!/bin/sh
set -eu
umask 077

fail() {
  printf 'Falix-Relay: %s\n' "$1" >&2
  exit 64
}

mode="${1:-run}"
case "$mode" in
  version)
    exec /usr/local/bin/xray version
    ;;
  run|check)
    ;;
  *)
    fail "usage: container [run|check|version]"
    ;;
esac

if [ -z "${XRAY_UUID:-}" ]; then
  fail "XRAY_UUID is required (set it as an environment variable)"
fi
if ! printf '%s' "$XRAY_UUID" | grep -Eq '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'; then
  fail "XRAY_UUID must be a UUID in 8-4-4-4-12 format"
fi

PORT="${PORT:-8080}"
case "$PORT" in
  ''|*[!0-9]*)
    fail "PORT must be a decimal TCP port between 1024 and 65535"
    ;;
esac
while [ "${PORT#0}" != "$PORT" ]; do PORT="${PORT#0}"; done
[ -n "$PORT" ] || PORT=0
if [ "${#PORT}" -gt 5 ] || [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
  fail "PORT must be between 1024 and 65535 (the container runs as non-root)"
fi

WS_PATH="${WS_PATH:-/relay}"
if ! printf '%s' "$WS_PATH" | grep -Eq '^/[A-Za-z0-9._~/-]+$'; then
  fail "WS_PATH must start with / and contain only letters, digits, /, dot, underscore, tilde or hyphen"
fi
case "$WS_PATH" in
  *..*|//*)
    fail "WS_PATH must not contain '..' or repeated leading slashes"
    ;;
esac

config_file="$(mktemp /tmp/falix-relay.XXXXXX.json)"
trap 'rm -f "$config_file"' EXIT HUP INT TERM
sed -e "s|__XRAY_UUID__|$XRAY_UUID|g" -e "s|__XRAY_PORT__|$PORT|g" -e "s|__XRAY_WS_PATH__|$WS_PATH|g" /etc/falix-relay/config.template.json > "$config_file"
if [ ! -s "$config_file" ]; then
  fail "failed to generate Xray configuration"
fi

if [ "$mode" = "check" ]; then
  /usr/local/bin/xray run -test -config "$config_file"
  exit $?
fi

printf 'Falix-Relay: starting official Xray-core on TCP port %s (WebSocket path %s)\n' "$PORT" "$WS_PATH"
exec /usr/local/bin/xray run -config "$config_file"
