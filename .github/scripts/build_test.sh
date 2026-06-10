#!/usr/bin/env bash

set -euo pipefail

root_directory="${ROOT_DIRECTORY:-.}"
url="http://127.0.0.1:6767"

python3 "${root_directory}"/bazarr.py --no-update &
PID=$!

cleanup() {
  echo "Stopping Bazarr..."
  pkill -INT -P "${PID}" 2>/dev/null || true
  kill -INT "${PID}" 2>/dev/null || true
  wait "${PID}" 2>/dev/null || true
}
trap cleanup EXIT

deadline=$((SECONDS + 120))

until curl -fsS --max-time 5 "${url}" --output /dev/null; do
  if ! kill -s 0 "${PID}" 2>/dev/null; then
    echo "Bazarr stopped before the UI became responsive."
    wait "${PID}" || true
    exit 1
  fi

  if (( SECONDS >= deadline )); then
    echo "Timed out waiting for Bazarr UI at ${url}."
    exit 1
  fi

  sleep 2
done

echo "UI is responsive."
