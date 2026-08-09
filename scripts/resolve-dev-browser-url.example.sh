#!/usr/bin/env bash
set -euo pipefail

workspace_root="${WORKSPACE_ROOT:-$(pwd)}"
forwarded_env="${workspace_root}/.dev/forwarded-ports.env"

if [[ -f "${forwarded_env}" ]]; then
  # The file is a user-owned workspace contract containing simple shell
  # assignments such as DEV_BROWSER_URL or DEV_LOCAL_PORT.
  # shellcheck disable=SC1090
  source "${forwarded_env}"
fi

if [[ -n "${DEV_BROWSER_URL:-}" ]]; then
  printf '%s\n' "${DEV_BROWSER_URL}"
  exit 0
fi

local_port="${DEV_LOCAL_PORT:-${DEV_APP_PORT:-}}"
if [[ -n "${local_port}" ]]; then
  printf 'http://localhost:%s/\n' "${local_port}"
  exit 0
fi

printf 'No forwarded development URL configured in %s\n' "${forwarded_env}" >&2
exit 1
