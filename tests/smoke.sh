#!/bin/sh
set -eu

IMAGE="${1:-falix-relay:test}"
UUID="00000000-0000-4000-8000-000000000001"
PREFIX="falix-relay-smoke-$$"

cleanup() {
  docker rm -f "${PREFIX}-server-port" "${PREFIX}-port-fallback" >/dev/null 2>&1 || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

fail() {
  printf 'Smoke test failed: %s\n' "$1" >&2
  exit 1
}

expect_rejected() {
  description="$1"
  shift

  if docker run --rm "$@" "$IMAGE" check >/dev/null 2>&1; then
    fail "invalid input was accepted: $description"
  fi
}

start_and_expect() {
  name="$1"
  expected_port="$2"
  shift 2

  docker run -d --name "$name" \
    -e "XRAY_UUID=$UUID" \
    "$@" \
    "$IMAGE" >/dev/null || fail "container did not start: $name"

  attempt=0
  while [ "$attempt" -lt 20 ]; do
    logs="$(docker logs "$name" 2>&1 || true)"
    if printf '%s' "$logs" | grep -Fq "TCP port $expected_port"; then
      printf 'Passed: %s listens on port %s\n' "$name" "$expected_port"
      return 0
    fi

    running="$(docker inspect --format '{{.State.Running}}' "$name" 2>/dev/null || printf false)"
    if [ "$running" != "true" ]; then
      printf '%s\n' "$logs" >&2
      fail "container exited before reporting its listening port: $name"
    fi

    attempt=$((attempt + 1))
    sleep 1
  done

  printf '%s\n' "$logs" >&2
  fail "timed out while waiting for startup: $name"
}

docker run --rm \
  -e "XRAY_UUID=$UUID" \
  -e SERVER_PORT=18443 \
  -e PORT=8080 \
  "$IMAGE" check

expect_rejected "invalid UUID" -e XRAY_UUID=invalid
expect_rejected "privileged port" -e "XRAY_UUID=$UUID" -e PORT=80
expect_rejected "invalid WebSocket path" -e "XRAY_UUID=$UUID" -e 'WS_PATH=/bad?path'

start_and_expect "${PREFIX}-server-port" 18443 \
  -e PORT=8080 \
  -e SERVER_PORT=18443 \
  -e WS_PATH=/server-port

start_and_expect "${PREFIX}-port-fallback" 18444 \
  -e PORT=18444 \
  -e WS_PATH=/port-fallback

printf 'All Falix-Relay smoke tests passed.\n'
