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

"${PY_BIN}" "${ROOT_DIR}/worker.py" "$@"
