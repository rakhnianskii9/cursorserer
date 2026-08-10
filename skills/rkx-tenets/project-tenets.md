# Project Tenets — portable workspace template

Guiding principles for `tenets_tenet` instill. Priority: critical = always inject.
Replace placeholder paths with the target workspace conventions after install.

## critical

- Communicate in English; system logs untranslated unless user asks.
- Never run `docker build` / `docker compose build` without explicit user request.
- Never revert git changes (`reset`, `restore`, `clean`, `checkout --`) without explicit user request.
- Persistence field/type changes require a migration registered in the owning migration index.
- New env keys only in the workspace env SoT after explicit user agreement; never commit secrets.
- Forensic Pass (canonical control-plane forensics rule): start with focused
  Read/search. Unknown scope → Tenets (narrow, fast); structural gap →
  CodeGraph or Octocode; DB gap → Postgres; Crash — synthesis as needed.
  Every stage is conditional; do not build a broad grep/search forest after Tenets rank/distill.
- `tenets_rank_files` on `${WORKSPACE_ROOT}`: only `mode=fast`, `top_n≤10`; `balanced`/`thorough` only on a pinned package folder. Never batch rank with CodeGraph/Octocode in one turn.
- A repeated full-repo rank in the same session is forbidden — use `tenets_session` + `pin_folder`. Run at most ≤6 `rank_files` in parallel; serialize full-repo runs.
- `tenets_distill` through MCP: pass `timeout: 45`, `max_tokens: 80000` explicitly (YAML does not reach tool defaults).
- UI verification: built-in @Browser only; no external browser, no Playwright MCP for evidence unless the user explicitly opts into that skill.

## high

- Use each package's declared UI stack; do not mix component systems across packages.
- New SQL columns and ORM column names: follow the workspace snake_case (or documented) convention.
- Out of scope zones: configure archival/export/tmp directories for the target workspace and keep them out of architecture answers.
- Docs: search `${WORKSPACE_ROOT}/docs` first; new module docs stay minimal and colocated with existing module docs.
- Prefer minimal diff; reuse existing patterns; no over-engineering.

## medium

- Timezone for dates: `${TZ}`.
- Filtered build: use the `package.json` `name`, not the directory name.
- Optional observability/sync labs stay opt-in skills, not default forensics.
- CodeGraph index: `.codegraph/codegraph.db`; run `codegraph sync` after large merges.

## low

- Tag degradation when MCP unavailable: `[DEGRADED: <surface>]`.
- Persist durable facts as compact, cited decisions in the living plan SoT or
  `loops/<run>/**`; no Memory MCP or `/memories/` store is configured.
