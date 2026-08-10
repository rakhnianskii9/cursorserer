---
name: octocode-code-forensics
description: >-
  Optional Octocode LSP and history support for explicit structural questions in
  ${WORKSPACE_ROOT}.
user-invocable: true
disable-model-invocation: false
---
# Code Forensics — graph+octocode pair

Use this skill for an explicit caller/impact/trace/LSP question or after
focused inspection reaches a real gap. It can be used independently from
CodeGraph; normal implementation never requires either tool.

- **CodeGraph** — fast monorepo map (trace, impact, routes)
- **Octocode** — precise verification (LSP, usages, call hierarchy, GitHub)

Start with the cheapest tool that answers the question. Tenets, CodeGraph,
Postgres, and Crash are independent optional evidence sources.

## Trigger Phrases

Load when the task explicitly asks:
- where defined / who calls it / how it flows
- impact before refactoring
- cross-module bugs
- route → service → DB or frontend → API → backend

## Optional structural workflow

```
- [ ] Load this skill; read the CodeGraph pair only if a graph question exists
- [ ] Known scope/anchors: choose focused Read, CodeGraph, or Octocode from the immediate gap
- [ ] Unknown scope: narrow `tenets_rank_files` (`mode=fast`) only after direct inspection fails
- [ ] If CodeGraph gives anchors and LSP precision matters, run Octocode `lspGetSemantics` → narrow Read
- [ ] Call `lspGetSemantics` with `uri`, exact `symbolName`, graph `lineHint`, and `type` = `definition` / `references` / `callers` / `callees` / `callHierarchy`
- [ ] Reconcile graph vs LSP only when both were used
- [ ] Read only for gaps or staleness
```

Focused search/read is valid before or instead of graph/LSP tools.

## Octocode Tool Routing

| Intent | Tool |
|--------|------|
| Resolve/verify symbol from graph hit | `lspGetSemantics` (`uri`, `symbolName`, `lineHint`, `type="references"`) |
| Verify callers | `lspGetSemantics` (`type="callers"`) |
| Verify callees | `lspGetSemantics` (`type="callees"`) |
| Walk execution | `lspGetSemantics` (`type="callHierarchy"`, `depth=1→N`) |
| External package | `npmSearch` → GitHub/content tools |
| PR history | `ghSearchPullRequests` |
| Confirm file section | `localGetFileContent` (narrow) |

Built-in fallback when Octocode MCP down: `#usages`, `search/usages`, `search/codebase` (narrow) — tag `[DEGRADED: octocode-mcp-unavailable]`.

## Handoff from CodeGraph

When a CodeGraph result leaves an LSP precision gap:
1. Take only the anchor symbols relevant to that gap
2. Run `lspGetSemantics` with its `uri`, exact `symbolName`, and graph `lineHint`
3. Flag mismatches only when they change the decision or reveal dynamic dispatch

## When Octocode Leads

Even if graph ran first, Octocode is **required** for:
- pre-rename / pre-delete verification
- PR/archaeology questions
- external library internals
- disputing graph staleness banner

If graph index missing: Octocode-only funnel allowed; tag `[DEGRADED: codegraph-index-missing]` and suggest `codegraph init -i`.

## Required Evidence

- evidence from the tools actually needed (or degradation tag)
- graph/LSP reconciliation only when both were used
- flow or blast radius only when requested
- uncertainty if the relevant chain is incomplete

## Output Contract

- relevant files + key symbols
- graph+octocode evidence log
- execution-flow summary
- impact/blast radius
- open uncertainty

## Pair Skill

`${CONTROL_PLANE_ROOT}/skills/rkx-codegraph/SKILL.md` (+ `project-map.md`, `recipes.md`)
