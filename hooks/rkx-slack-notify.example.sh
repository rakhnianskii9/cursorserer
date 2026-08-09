#!/usr/bin/env bash
# Cursor stop hook → run-scoped RKX Slack notification card.
#
# The helper reads loops/<run>/slack-notification.json and never derives
# user-facing text from the globally newest state.md. It is deliberately
# fail-open: a missing artifact or Slack outage must not break Cursor.
#
# Env (${HOME}/.cursor/rkx-slack-notify.env):
#   SLACK_WEBHOOK_URL       Incoming Webhook
#   SLACK_BOT_TOKEN         bot token with chat:write
#   SLACK_NOTIFY_CHANNEL    required with bot token
#   RKX_SLACK_NOTIFY_MODE   attention_and_result | attention | result
#                           (all/events/terminal_only are compatibility aliases)
#   RKX_SLACK_DEDUP_SEC     delivered-event window in seconds (default: artifact max age)
#   RKX_SLACK_PENDING_SEC   in-flight lease in seconds (default: 120)
#   RKX_SLACK_NOTIFICATION_MAX_AGE_SEC (default: 1800)

set -euo pipefail

ENV_FILE="${HOME}/.cursor/rkx-slack-notify.env"
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
  # User-level hooks resolve the repository from workspace_roots in the
  # Cursor event payload instead of assuming ${HOME}/.cursor is the repository.
  unset RKX_REPO_ROOT
fi

# Stop hooks are notifications only. Never fail the Cursor stop because the
# renderer, artifact, or outbound Slack transport is unavailable.
set +e
PYTHON_HOOK="${SCRIPT_DIR}/rkx_slack_notify.py"
if [[ ! -f "${PYTHON_HOOK}" ]]; then
  PYTHON_HOOK="${SCRIPT_DIR}/rkx_slack_notify_example.py"
fi
python3 "${PYTHON_HOOK}"
exit 0
