---
name: graph-octocode
description: "Use for cross-package forensics and pre-edit impact analysis: CodeGraph maps flow; Octocode verifies exact symbols, references, call hierarchy, and external history."
user-invocable: true
disable-model-invocation: false
---

# graph-octocode

Use this optional forensic pass for explicit cross-module trace or impact work.
A known-file read—or targeted search for an ordinary edit—does not require it.

## Routing

Choose the cheapest path that answers the question:

1. One known file and no structural question → built-in `Read`.
2. Use one of CodeGraph, Octocode, or Read based on the immediate question.
3. Use Tenets only if targeted search cannot identify a broad scope.
4. Add another tool only if the current evidence leaves a concrete gap.
5. Read the precise source range when it is the fastest evidence.

CodeGraph is a pre-existing read-only index. This workflow queries it; it does not rebuild the graph.

## Division of labour

| Need | Use |
|---|---|
| Architecture, route and cross-package trace | CodeGraph |
| Precise TS symbols, rename safety, callers/callees | Octocode LSP |
| External package internals or PR history | Octocode + Context7 if applicable |
| Database evidence | read-only Postgres after the flow is narrowed |

If either MCP is unavailable, use the narrowest available evidence source.
