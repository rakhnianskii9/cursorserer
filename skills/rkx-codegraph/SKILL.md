---
name: rkx-codegraph
description: >-
  Optional CodeGraph support for explicit structural, impact, and trace questions
  in ${WORKSPACE_ROOT}.
user-invocable: true
disable-model-invocation: false
---
# CodeGraph — workspace (graph+octocode pair)

Use this skill only for an explicit structural/impact/trace request or when
focused Read/search is blocked. It can be used alone; Octocode is optional for
a precise LSP question. Normal edits do not need either tool.

- **CodeGraph** — map: architecture, trace, impact, routes, cross-package flow
- **Octocode** — verification: LSP refs/call hierarchy, exact usages, GitHub/external packages

For an unknown scope, start with targeted search; use Tenets only if that
cannot identify the target. Crash and Postgres are optional evidence tools.

## Trigger Phrases

Load when the USER explicitly asks about:
- how does X work / where is X defined / who calls X
- trace flow route/API/UI → service/worker/DB
- impact / blast radius before editing
- feature map across application packages (API, UI, workers, shared libs)

## Preconditions

1. Index: `${WORKSPACE_ROOT}/.codegraph/codegraph.db` (if missing, ask the user → `codegraph init -i`)
2. MCP: `codegraph` (`${HOME}/.cursor/mcp.json` — Cursor MCP)
3. Read `${CONTROL_PLANE_ROOT}/skills/octocode-code-forensics/SKILL.md` and use Octocode only when an LSP or history gap requires it

```bash
codegraph status ${WORKSPACE_ROOT}
```

## Optional graph workflow

```
- [ ] Ask the smallest structural question with CodeGraph.
- [ ] Add Octocode only if LSP precision resolves a real gap.
- [ ] Read the exact source range if needed.
```

Typical session starts with one targeted CodeGraph call; add only the minimum follow-up needed to close the current gap.

## CodeGraph Tool Matrix

| Intent | Tool |
|--------|------|
| Map task area | `codegraph_context` |
| A → B call chain | `codegraph_trace` |
| Survey symbols | `codegraph_explore` |
| Find by name | `codegraph_search` |
| Callers / callees | `codegraph_callers` / `codegraph_callees` |
| Pre-edit blast radius | `codegraph_impact` |
| Symbol detail | `codegraph_node` |
| Indexed tree | `codegraph_files` |
| Index health | `codegraph_status` |

## Optional Octocode handoff (after graph)

| Graph gave | Octocode confirms |
|------------|-------------------|
| Symbol name + file from `codegraph_node` | `lspGetSemantics` with `references` or `callHierarchy` |
| Cross-file flow from `codegraph_trace` | `localGetFileContent` on hop boundaries only if stale |
| Impact list from `codegraph_impact` | `lspGetSemantics(type="references")` on top-risk symbols |
| External/lib boundary | Octocode `npmSearch` / GitHub tools |
| PR/archaeology | `ghSearchPullRequests` |

## Division of Labor (not fallback)

| Layer | Owner |
|-------|-------|
| Workspace graph, routes, workers, cross-package trace | **codegraph** |
| Precise TS references, rename safety, call hierarchy depth | **octocode `lspGetSemantics`** |
| External npm / GitHub history | **octocode** (+ context7) |
| Simple Read one known file | built-in Read (skip graph) |

## Workspace Scope

See [project-map.md](project-map.md). Key zones are placeholders filled from the
target workspace: API/route packages, workers/queues, primary UI packages, and
shared libs.

**Out of scope:** archival/export/tmp directories configured for the target workspace.

## Domain Playbooks (graph → octocode)

### Route → handler → service
1. `codegraph_search` (`kind=route`) → `codegraph_trace`
2. Add Octocode `lspGetSemantics(type="callHierarchy")` only if call precision changes the answer

### Background jobs / workers
1. `codegraph_context` (worker + queue)
2. `codegraph_trace` to the local coordinator/processor symbols
3. Add Octocode `lspGetSemantics(type="references")` only for an unresolved usage or rename-safety gap

### Entity / migration
1. `codegraph_search` Entity/model + migration
2. `codegraph_impact` on entity
3. Add Octocode refs only when the graph impact set leaves a concrete gap

### Cross-package (frontend → API)
1. `codegraph_trace` UI hook → route handler
2. Add Octocode `lspGetSemantics(type="references")` only if API client usages are disputed

## Staleness

Pending-file banner → `Read` live file + `codegraph sync`; Octocode LSP on synced content.

## Degradation

| Missing | Action |
|---------|--------|
| codegraph MCP | CLI `codegraph …` + full octocode funnel; tag `[DEGRADED: codegraph-mcp-unavailable]` |
| octocode MCP | graph-only + built-in `#usages`/`search/usages`; tag `[DEGRADED: octocode-mcp-unavailable]` |
| both | narrowed Read + tag `[DEGRADED: graph+octocode-unavailable]` |

## Output Contract

- graph or Octocode evidence actually used
- reconciled flow/impact only when both sources were needed
- uncertainty (stale, dynamic dispatch, MCP degradation)

## Resources

- [project-map.md](project-map.md), [recipes.md](recipes.md)
- Pair skill: `${CONTROL_PLANE_ROOT}/skills/octocode-code-forensics/SKILL.md`
- Docs: https://colbymchenry.github.io/codegraph/reference/mcp-server/
