#!/usr/bin/env bash
# Validate the portable RKX control plane without external services.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

python3 "${SCRIPT_DIR}/validate_rkx_loops.py"
python3 "${SCRIPT_DIR}/validate-rkx-blueprint-coverage.py"
python3 "${SCRIPT_DIR}/validate-rkx-blueprint-coverage.py" --require-results
python3 "${ROOT}/hooks/test_rkx_slack_notify.py"
python3 "${SCRIPT_DIR}/test_scheme_scenarios.py"
