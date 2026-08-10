#!/usr/bin/env bash
# Cursor afterFileEdit hook → immediate RKX Slack delivery on artifact write.
#
# Fires as soon as loops/<run>/slack-notification.json is written/edited.
# Normalizes common kind/notification_type mistakes, then delivers with retries.
# Fail-open: never blocks the agent edit path.

set -euo pipefail

ENV_FILE="${HOME}/.cursor/rkx-slack-notify.env"  # local secrets; not shipped
if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "${ENV_FILE}"
  set +a
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "${RKX_REPO_ROOT:-}" && -d "${RKX_REPO_ROOT}/loops" ]]; then
  export RKX_REPO_ROOT
elif [[ -d "${SCRIPT_DIR}/../../loops" ]]; then
  export RKX_REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
else
  unset RKX_REPO_ROOT
fi

set +e
python3 "${SCRIPT_DIR}/rkx_slack_notify.py" --on-write
exit 0
