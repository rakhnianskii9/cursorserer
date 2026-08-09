# Project Tenets — workspace

Guiding principles for `tenets_tenet` instill. Priority: critical = always inject.

## critical

- Communicate in English; system logs untranslated unless user asks.
- Never run `docker build` / `docker compose build` without explicit user request.
- Never revert git changes (`reset`, `restore`, `clean`, `checkout --`) without explicit user request.
- Entity field/type changes require an ORM migration registered in the owning database migration index.
- New env keys only in `docker/.env` after explicit user agreement; never commit secrets.
- Forensic Pass (canonical rule `infrastructure-core.mdc §3.2`): start with focused
  Read/search. Unknown scope → Tenets (narrow, fast); structural gap →
  CodeGraph or Octocode; DB gap → Postgres; Crash — synthesis as needed.
  Every stage is conditional; do not build a broad grep/search forest after Tenets rank/distill.
- `tenets_rank_files` on `${WORKSPACE_ROOT}`: only `mode=fast`, `top_n≤10`; `balanced`/`thorough` only on `packages/*` or a pinned folder. Never batch rank with CodeGraph/Octocode in one turn.
- A repeated full-repo rank in the same session is forbidden — use `tenets_session` + `pin_folder`. Run at most ≤6 `rank_files` in parallel; serialize full-repo runs.
- `tenets_distill` through MCP: pass `timeout: 45`, `max_tokens: 80000` explicitly (YAML does not reach tool defaults).
- UI verification in frontend/admin-ui/messaging: built-in @Browser only; no external browser, no Playwright MCP for evidence.

## high

- Use each package's declared UI stack; do not mix component systems across packages.
- New SQL columns and `@Column({ name })`: snake_case.
- Out of scope zones: `x-old-projects/`, `user-export/`, `code-export/`, `tmp/`.
- Docs: search `${WORKSPACE_ROOT}/docs` first; new module doc max one `.md` in `docs/moduls`.
- Prefer minimal diff; reuse existing patterns; no over-engineering.

## medium

- Timezone for dates: `${TZ}`.
- Filtered build: use the `package.json` `name`, not the directory name.
- Background sync tuning: use an optional workspace sync-lab skill + markdown ledger if configured.
- CodeGraph index: `.codegraph/codegraph.db`; run `codegraph sync` after large merges.

## low

- Tag degradation when MCP unavailable: `[DEGRADED: <surface>]`.
- Persist durable facts as compact, cited decisions in the living plan SoT or
  `loops/<run>/**`; no Memory MCP or `/memories/` store is configured.
