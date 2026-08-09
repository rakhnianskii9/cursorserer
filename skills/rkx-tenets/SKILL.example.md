---
name: rkx-tenets
description: >-
  Optional Tenets context discovery for an unknown code scope in
  ${WORKSPACE_ROOT}.
user-invocable: true
disable-model-invocation: false
---
# Tenets — token-efficient context (tier 0)

Use Tenets only after focused Read/search cannot identify the target scope.
It is not a default discovery step and does not require graph tools afterward.

**Conditional forensics stack:** when the scope is unknown or broad, `tenets`
narrow it. Then choose CodeGraph, Octocode, or surgical `Read` only for the
remaining concrete gap. Skip Tenets when the files/symbols are already known.

## Trigger Phrases

Load only when:
- the code area is unknown or broad
- context is needed for a feature/bug/refactor/review
- the session is long and context drift is a risk
- before Planning/Implement — narrow the scope

For explicit trace/impact/LSP work, choose CodeGraph or Octocode only when it
answers the current question; Tenets does not make that chain mandatory.

## Preconditions

1. MCP `tenets` in `${HOME}/.cursor/mcp.json` (Cursor Settings → MCP)
2. Binary: `${WORKSPACE_ROOT}/.tenets/venv/bin/tenets-mcp`
3. Config: `${WORKSPACE_ROOT}/.tenets.yml`
4. Project tenets: [project-tenets.md](project-tenets.md)

```bash
${WORKSPACE_ROOT}/.tenets/venv/bin/tenets-mcp --version
```

## Optional discovery workflow

```
- [ ] Load this skill (+ graph+octocode skills if forensics)
- [ ] tenets_tenet action=instill — project rules from project-tenets.md (once per session)
- [ ] tenets_session action=create — multi-turn tasks; pin_folder on active module
- [ ] tenets_rank_files (mode=fast, narrow path) — discovery; tenets_distill — rich context for top paths
- [ ] choose CodeGraph or Octocode on tenets-ranked files only for a structural
      gap; add the other only if needed
- [ ] Read — only gaps, staleness, or post-change verify
```

**Observed timings (workspace, ~3.1k files after excludes):** `fast` on `packages/<mod>/` — seconds; `fast` on the full repo — **up to ~60 s**; `balanced` on the full repo — **minutes, timeout risk**. The “~500ms” claim is true only for a **narrow** path.

Start with targeted search even for a broad request. Use ranking only when that
search leaves the scope genuinely unknown; direct Read/search remains valid.

## Anti-patterns (always-fast)

- `rank_files`/`distill` on the full workspace in `balanced` — **forbidden** (minutes); full repo only `mode=fast`, `top_n≤10`, as a last resort.
- Do not batch `tenets_rank_files` ∥ `codegraph_*`/`octocode` in one turn — wait for `files[]` first, then run the graph on the top paths.
- **Concurrency limit: ≤6 simultaneous `rank_files`; serialize full-repo runs** (stress 47× → p95 ~166 s, 22/47 ok).
- Do not repeat a full-repo rank in the same session — use `tenets_session` + `pin_folder`, then distill with `session=`.
- `explain=true` — only for debugging an empty/low score, not routinely.
- Do not rely on the IDE cwd: MCP starts through `.tenets/run-mcp.sh` + `TENETS_PROJECT_ROOT`; without this, `.tenets.yml` is not loaded.
- Do not call `distill` on the root before `rank_files` — get the top paths first, then distill those paths.

## Path / Mode Contract (workspace)

Monorepo ~3.1k files after excludes. Time = **path × mode**, not an average “~500ms”.

| Scope | path | mode | top_n |
|-------|------|------|-------|
| Module known (server, frontend, messaging, admin-ui, docker) | `packages/<pkg>/…` or `docker/` | `fast` | 8–12 |
| Module unknown — initial discovery | `packages/` (not the root) | `fast` | 10–15 |
| Full repo | `${WORKSPACE_ROOT}` | `fast` only, last resort | ≤10 |
| Full repo + `balanced`/`thorough` | — | **forbidden** without approval | — |
| After `pin_folder` | pinned folder | `balanced` is OK | 8–12 |

**MCP arg override (critical):** tool defaults — `mode=balanced`, `timeout=120`, `max_tokens=100000` — **override** `.tenets.yml`. Therefore, set these **explicitly** in calls: `mode: "fast"`; for `tenets_distill`, also set `timeout: 45`, `max_tokens: 80000`.

**Path rules:** `include_patterns` does **not** replace a narrow `path` (the scanner still walks the tree). If full-repo returns `files: []`, retry with `packages/<module>/`; do not repeat full-repo. If an infrastructure path is external to the workspace, use the repository's runtime configuration or prompt instead of assuming a host path.

## Tool Matrix

| Intent | Tool | When |
|--------|------|------|
| Fast file list | `tenets_rank_files` | Unknown scope: `path=packages/<mod>/` + `mode=fast`; full repo as a last resort; do not batch with CodeGraph in one turn |
| Optimized context blob | `tenets_distill` | Need code bodies ranked by relevance |
| Discover tools on-demand | `tenets_search_tools` → `tenets_get_tool_schema` | Meta-tools; ~80% less upfront schema tokens |
| Codebase overview | `tenets_examine` | Onboarding, architecture survey |
| Recent changes | `tenets_chronicle` | Bug after merge, «who changed X» |
| Dev velocity | `tenets_momentum` | Sprint/activity questions |
| Multi-turn pin | `tenets_session` (create/list/pin_file/pin_folder) | Feature spanning multiple agent turns |
| Project rules injection | `tenets_tenet` (add/list/instill) | Prevent drift from code-rules |
| One-shot instruction | `tenets_system_instruction` | Session-specific behavioral nudge |

## Handoff to graph+octocode

After `tenets_rank_files` or `tenets_distill` (or immediately if the anchors are already known):

1. Take **top 3–10 paths** from Tenets output, or use paths already known from the task
2. Pass those paths as anchors into `codegraph_context` / `codegraph_search` (narrow scope)
3. Octocode `lspGetSemantics` on symbols from graph — with real `uri`, `symbolName`, and `lineHint`
4. Do **not** re-read files Tenets already distilled unless stale banner

| Tenets gave | graph+octocode does |
|-------------|---------------------|
| Ranked file list | `codegraph_trace` / `codegraph_impact` on those files |
| Distill context blob | Verify symbols via Octocode LSP; graph for cross-package hops |
| Session pinned folder | Limit graph search to pinned paths |

## Forensic Pass (canonical pattern)

Tenets is stage zero of the overall **Forensic Pass** (canonical rule in `infrastructure-core.mdc §3.2`):

> **Unknown scope:** direct search → Tenets (narrow scope, fast) → choose
> CodeGraph, Octocode, Postgres, or Read only for the next named gap.
> **Known scope:** direct Read/search first; add a graph/LSP/DB tool only
> when its specific capability is needed.
> **Crash** — a cross-cutting synthesis layer used when needed.

Every stage is **conditional** — do not run everything in sequence for a trivial task. Tenets
is for discovery only; ≤6 parallel `rank_files`; serialize full-repo runs.

## Session Protocol (multi-turn)

```text
1. tenets_session action=create name=<task-slug>
2. tenets_session action=pin_folder path=packages/frontend/src/...  (active module)
3. Each turn: distill uses pinned files automatically
4. On task complete: note session name in handoff for continuity
```

## Project Tenets (instill once per session)

Call `tenets_tenet` action=`instill` with principles from [project-tenets.md](project-tenets.md), or add critical ones via action=`add` priority=`critical`.

Key injected rules (summary):
- English comms; no Docker build without explicit user request
- frontend/admin-ui: use each package's declared UI stack; do not mix systems
- Entity changes → migration + postgres registry
- Forensics: tenets → graph+octocode; no broad grep first
- UI evidence: built-in @Browser only

## Division of Labor

| Layer | Owner | Token role |
|-------|-------|------------|
| Broad relevance ranking | **tenets** | Replaces 10–50 blind Reads |
| Monorepo graph/trace/impact | **codegraph** | Structural map on narrowed set |
| LSP/refs/call hierarchy | **octocode** | Precision on graph anchors |
| External library docs | **context7** | After code context known |
| Single known file | built-in Read | Skip tenets, graph, and Octocode |
| Known files/symbols | Focused Read/search; CodeGraph or Octocode only for a named structural gap | Skip Tenets ranking |
| Subagent / Task slice | **inherits** the parent `tenets_session` + handoff paths | **Forbidden:** independent full-repo rank/distill (N× scan on one stdio) |

## Degradation

| Missing | Action |
|---------|--------|
| tenets MCP | graph+octocode funnel directly; tag `[DEGRADED: tenets-mcp-unavailable]` |
| tenets + codegraph | octocode + narrow Read; tag both degradations |
| all three | minimal Read + `[DEGRADED: tenets+graph+octocode-unavailable]` |
| tenets slow / timeout | narrow `path` to `packages/<module>/`, `mode=fast`; **do not** escalate to `balanced`/`thorough` on the full repo |

## Output Contract

- tenets tools called + top files returned, if discovery was used
- token_count from distill (if used)
- graph+octocode evidence on tenets-narrowed scope
- degradation tags if any

## Resources

- [project-tenets.md](project-tenets.md)
- Pair: `${CONTROL_PLANE_ROOT}/skills/rkx-codegraph/SKILL.md` + `${CONTROL_PLANE_ROOT}/skills/octocode-code-forensics/SKILL.md`
- Docs: https://tenets.dev/latest/MCP/
