#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_BIN="${PYTHON_BIN:-python3}"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "${ROOT_DIR}/.env"
  set +a
fi

echo "[starter] launching Clash Royale API proxy..."
"${PY_BIN}" "${ROOT_DIR}/api.py" &
API_PID=$!

echo "[starter] launching worker in background..."
"${PY_BIN}" "${ROOT_DIR}/worker.py" "$@" &
WORKER_PID=$!

cleanup() {
  echo "[starter] stopping worker/api"
  for PID in "${WORKER_PID}" "${API_PID}"; do
    if ps -p "${PID}" >/dev/null 2>&1; then
      kill "${PID}" >/dev/null 2>&1 || true
    fi
  done
}
trap cleanup EXIT

echo "[starter] serving frontend on http://localhost:3000 (Ctrl+C to stop)"
cd "${ROOT_DIR}"
"${PY_BIN}" -m http.server 3000
