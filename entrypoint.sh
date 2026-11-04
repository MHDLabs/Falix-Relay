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

if [ "$#" -gt 1 ]; then
  fail "only one command is supported: run, check, or version"
fi

if [ -z "${XRAY_UUID:-}" ]; then
  fail "XRAY_UUID is required (set it as an environment variable)"
fi

if ! printf '%s' "$XRAY_UUID" | grep -Eq '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'; then
  fail "XRAY_UUID must be a UUID in 8-4-4-4-12 format"
fi

if [ "$XRAY_UUID" = "00000000-0000-4000-8000-000000000001" ]; then
  fail "replace the example XRAY_UUID with your own private UUID"
fi

# Falix injects SERVER_PORT. Prefer it over the generic PORT fallback.
PORT="${SERVER_PORT:-${PORT:-8080}}"
case "$PORT" in
  ''|*[!0-9]*)
    fail "PORT or SERVER_PORT must be a decimal TCP port between 1024 and 65535"
    ;;
esac

while [ "${PORT#0}" != "$PORT" ]; do
  PORT="${PORT#0}"
done
[ -n "$PORT" ] || PORT=0

if [ "${#PORT}" -gt 5 ] || [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
  fail "PORT or SERVER_PORT must be between 1024 and 65535 (the container runs as non-root)"
fi

WS_PATH="${WS_PATH:-/relay}"
if ! printf '%s' "$WS_PATH" | grep -Eq '^/[A-Za-z0-9._~/-]+$'; then
  fail "WS_PATH must start with / and contain only letters, digits, /, dot, underscore, tilde or hyphen"
fi

case "$WS_PATH" in
  *..*|//*)
    fail "WS_PATH must not contain '..' or repeated slashes"
    ;;
esac

config_dir="$(mktemp -d /tmp/falix-relay.XXXXXX)"
config_file="$config_dir/config.json"

cleanup() {
  rm -rf "$config_dir"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

sed \
  -e "s|__XRAY_UUID__|$XRAY_UUID|g" \
  -e "s|__XRAY_PORT__|$PORT|g" \
  -e "s|__XRAY_WS_PATH__|$WS_PATH|g" \
  /etc/falix-relay/config.template.json > "$config_file"

if [ ! -s "$config_file" ]; then
  fail "failed to generate Xray configuration"
fi

if [ "$mode" = "check" ]; then
  if /usr/local/bin/xray run -test -config "$config_file"; then
    exit 0
  else
    status=$?
    exit "$status"
  fi
fi

printf 'Falix-Relay: starting official Xray-core on TCP port %s (WebSocket path %s)\n' "$PORT" "$WS_PATH"

/usr/local/bin/xray run -config "$config_file" &
xray_pid=$!

# Invoked indirectly by the HUP, INT and TERM traps.
# shellcheck disable=SC2317
forward_signal() {
  kill -s "$1" "$xray_pid" 2>/dev/null || true
}
trap 'forward_signal HUP' HUP
trap 'forward_signal INT' INT
trap 'forward_signal TERM' TERM

status=0
while :; do
  if wait "$xray_pid"; then
    status=0
  else
    status=$?
  fi

  if ! kill -0 "$xray_pid" 2>/dev/null; then
    break
  fi
done

exit "$status"
