#!/bin/sh
set -eu

IMAGE="${1:-falix-relay:test}"
UUID="11111111-1111-4111-8111-111111111111"
PREFIX="falix-relay-smoke-$$"

cleanup() {
  docker rm -f "${PREFIX}-server-port" "${PREFIX}-port-fallback" "${PREFIX}-empty-server-port" >/dev/null 2>&1 || true
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
      if printf '%s' "$logs" | grep -Fq "$UUID"; then
        fail "container leaked the client UUID in its logs: $name"
      fi
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

stop_and_expect() {
  name="$1"

  docker stop --time 5 "$name" >/dev/null || fail "container did not stop: $name"
  exit_code="$(docker inspect --format '{{.State.ExitCode}}' "$name")"

  if [ "$exit_code" -eq 137 ]; then
    fail "container ignored SIGTERM and required SIGKILL: $name"
  fi

  printf 'Passed: %s stopped without SIGKILL (exit %s)\n' "$name" "$exit_code"
}

version_output="$(docker run --rm "$IMAGE" version)"
printf '%s' "$version_output" | grep -Fq "26.10.31" || fail "unexpected Xray version: $version_output"

expect_rejected "missing UUID"
expect_rejected "invalid UUID" -e XRAY_UUID=invalid
expect_rejected "public example UUID" -e XRAY_UUID=00000000-0000-4000-8000-000000000001
expect_rejected "privileged fallback port" -e "XRAY_UUID=$UUID" -e PORT=80
expect_rejected "privileged Falix port" -e "XRAY_UUID=$UUID" -e SERVER_PORT=80 -e PORT=18443
expect_rejected "invalid WebSocket path" -e "XRAY_UUID=$UUID" -e 'WS_PATH=/bad?path'
expect_rejected "path traversal" -e "XRAY_UUID=$UUID" -e 'WS_PATH=/../relay'
expect_rejected "repeated WebSocket slashes" -e "XRAY_UUID=$UUID" -e 'WS_PATH=/relay//extra'

docker run --rm \
  -e "XRAY_UUID=$UUID" \
  -e SERVER_PORT=18443 \
  -e PORT=8080 \
  "$IMAGE" check

start_and_expect "${PREFIX}-server-port" 18443 \
  -e PORT=8080 \
  -e SERVER_PORT=18443 \
  -e WS_PATH=/server-port

start_and_expect "${PREFIX}-port-fallback" 18444 \
  -e PORT=18444 \
  -e WS_PATH=/port-fallback

start_and_expect "${PREFIX}-empty-server-port" 18445 \
  -e PORT=18445 \
  -e SERVER_PORT= \
  -e WS_PATH=/empty-server-port

stop_and_expect "${PREFIX}-server-port"
stop_and_expect "${PREFIX}-port-fallback"
stop_and_expect "${PREFIX}-empty-server-port"

printf 'All Falix-Relay smoke tests passed.\n'
