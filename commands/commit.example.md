---
description: Draft git commit (only if USER asked)
---
# /commit

> **Cursor control-plane:** `${CONTROL_PLANE_ROOT}/` for Cursor IDE.

Anti-hijack scribe: draft the commit without committing automatically. Follow
the repository rules (`${CONTROL_PLANE_ROOT}/rules/rkx-always-on.mdc` → “Secrets / env / git”).

## Hard gates

- **Do not commit** until the USER explicitly asks (“commit” / “commit this”).
  Rule: “Commit only if USER asked.”
- Never use `git reset` without the USER’s explicit permission.
- Never use `--no-verify` / `--no-gpg-sign`; never bypass hooks.
- No secrets, tokens, passwords, or `.env` files in the diff or message.
  Approved env keys belong only in `docker/.env`.

## Workflow

1. `git status` + `git diff --staged` — inspect what is actually staged. If
   staging is empty, ask the USER what to stage; do not stage blindly.
2. Scan the staged diff for secrets (keys, tokens, `process.env.*` values,
   `password`, `secret`, `API_KEY`). Any hit → STOP and show the USER.
3. Draft the message: **why > what** — motivation/context first, mechanics
   second. No filler or technical detail for its own sake.
4. Repository style (from `git log`):
   - routine work — a short English line (`postgres July 25 at 14:00`, `database
     cleanup`, `loops`);
   - feature work — `rkx NNN - <area> #N and <area> #N: <summary>` plus a body
     grouped by subsystem.
5. Use HEREDOC for a multiline message (`git commit -F-` or
   `$(cat <<'EOF' … EOF)`), NOT multiple `-m` flags.

## Before committing

- Show the USER the message draft and the list of staged files.
- Commit only after an explicit “OK / proceed / commit”.
- After committing, run `git log -1 --stat` for confirmation.
