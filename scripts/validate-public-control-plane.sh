#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

case "${1:-}" in
  --archive)
    exec python3 "${SCRIPT_DIR}/validate-public-control-plane.py" --archive
    ;;
  --runtime)
    python3 "${SCRIPT_DIR}/validate-public-control-plane.py" --runtime
    if [[ -f "${SCRIPT_DIR}/validate_rkx_loops.py" ]]; then
      python3 "${SCRIPT_DIR}/validate_rkx_loops.py"
    fi
    if [[ -f "${SCRIPT_DIR}/validate-rkx-blueprint-coverage.py" ]]; then
      python3 "${SCRIPT_DIR}/validate-rkx-blueprint-coverage.py"
      python3 "${SCRIPT_DIR}/validate-rkx-blueprint-coverage.py" --require-results
    fi
    if [[ -f "${ROOT}/hooks/test_rkx_slack_notify.py" ]]; then
      python3 "${ROOT}/hooks/test_rkx_slack_notify.py"
    fi
    if [[ -f "${SCRIPT_DIR}/test_scheme_scenarios.py" ]]; then
      python3 "${SCRIPT_DIR}/test_scheme_scenarios.py"
    fi
    ;;
  *)
    printf 'Usage: %s --archive|--runtime\n' "$0" >&2
    exit 2
    ;;
esac
