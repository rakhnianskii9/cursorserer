#!/usr/bin/env bash
set -euo pipefail

workspace_root="${WORKSPACE_ROOT:-$(pwd)}"
forwarded_env="${workspace_root}/.dev/forwarded-ports.env"

if [[ -f "${forwarded_env}" ]]; then
  # The file is a user-owned workspace contract containing simple shell
  # assignments for forwarded development ports.
  # shellcheck disable=SC1090
  source "${forwarded_env}"
fi

found=0
for variable in DEV_LOCAL_PORT DEV_APP_PORT AUX_APP_PORT_A AUX_APP_PORT_B AUX_APP_PORT_C; do
  if [[ -n "${!variable:-}" ]]; then
    printf '%s=%s\n' "${variable}" "${!variable}"
    found=1
  fi
done

if [[ "${found}" -eq 0 ]]; then
  printf 'No development ports configured in %s\n' "${forwarded_env}" >&2
  exit 1
fi
