---
name: rkx-mcp-utilities
description: >-
  Utility MCP routing for workspace: context7, crash, postgres, figma, kaggle,
  mcp-files, stitch. Load when task needs external docs, structured reasoning, DB
  evidence, design-to-code, datasets, surgical file ops, or Google Stitch. Use
  direct inspection first; Tenets is only for an unknown code scope.
user-invocable: true
disable-model-invocation: false
---
# Utility MCP — workspace

Routing skill for the **7 utility MCPs** installed in `${HOME}/.cursor/mcp.json` (Cursor Settings → MCP).

Start with direct targeted Read/search. For unknown scope, load `rkx-tenets`; for a structural gap, use CodeGraph or Octocode; then load this skill only for a matching utility trigger.

**Forensic routing (canonical: rule `rkx-forensics`):** Tenets is conditional discovery, CodeGraph/Octocode are conditional structural tools, and Postgres is conditional DB evidence. **Crash** is a cross-cutting synthesis layer for competing hypotheses, large evidence bundles, or bounded review. No tool sequence is unconditional.

Configuration: `${HOME}/.cursor/mcp.json`.

## Trigger Matrix

| MCP | When to load the skill / call it | Primary tools |
|---|---|---|
| **crash** | Competing hypotheses, orchestration, Merger synthesis of large chat/slot bundles, Boss review | `crash/crash` |
| **context7** | External library/API docs **after** Tenets has narrowed the code | `context7/resolve-library-id`, `context7/query-docs` |
| **postgres** | Entity/migration/SQL, FK validation, read-only schema/data | `postgres/query` |
| **figma** | User provided a figma.com URL, design-to-code, Code Connect | `figma/get_design_context`, `figma/get_screenshot` |
| **kaggle** | Benchmarks, datasets, ML references (rare in this project) | `kaggle/search_*`, `kaggle/get_*` |
| **mcp-files** | Surgical byte-offset edit / symbol read when built-in editing is insufficient | `mcp-files/*` |
| **stitch** | Google Stitch design/generation (requires an API key) | HTTP MCP after auth |

**Not part of the “7 utility” set:** provider developer tools MCP → a separate
domain skill. Triggers: provider app config, rate limits, review, compliance,
webhook subscribe/test, provider docs/changelog. Do not use this skill as a
replacement for the forensics chain.

## crash — structured reasoning

Use Crash after the currently relevant evidence is available; it does not require
Tenets, a graph pass, or a fixed loop phase. Merger uses it to synthesize large
chat/slot bundles; Boss uses it to challenge the Merger state. Pass artifact
references and the unresolved delta, not a repeated raw archive.

```
- [ ] Current scope, evidence gap, and decision to unblock
- [ ] Relevant artifact references and new/contradicting evidence only
- [ ] Structured synthesis before L1 STOP or bounded review
```

Degradation: `[DEGRADED: crash-unavailable]` → plain structured prose.

## context7 — external docs

**After** Tenets/code context is known — not before.

| Intent | Flow |
|---|---|
| Implement with npm lib | `resolve-library-id` → `query-docs` |
| Verify API version/migration | topic-specific `query-docs` |
| Best practice check | `query-docs` with library + topic |

Env: `CONTEXT7_API_KEY` (set in `${HOME}/.cursor/mcp.json`).

Degradation: `web/fetch` official docs + `[DEGRADED: context7-unavailable]`.

## postgres — read-only DB evidence

**Read-only** unless user explicitly approved schema mutations.

| Intent | Example query pattern |
|---|---|
| FK type check | `\d table_name` or information_schema |
| Column exists | `SELECT column_name FROM information_schema.columns WHERE ...` |
| Row count sanity | `SELECT COUNT(*) FROM ... LIMIT context` |
| Migration verify | Compare entity columns vs `\d` output |

Connection: the private user-level `${HOME}/.cursor/mcp.json` must supply a resolved
runtime URI. Never place the URI or credentials in this repository.

Pair with: workspace security rules on auth/SQL tasks; use the target project's
migration guidance for schema changes.

Degradation: `[DEGRADED: postgres-unavailable]` → code-only Entity/migration files.

## figma — design-to-code

Trigger: user shares `figma.com/design/...` URL.

```
- [ ] Parse fileKey + nodeId from URL
- [ ] get_design_context → adapt to the target package's declared UI stack
- [ ] Reuse existing components; do not paste raw Tailwind dump blindly
- [ ] get_screenshot for visual diff if needed
```

Pair with the target package's design-system and UI-consistency skills when configured.

## kaggle — data/ML platform

Use **only** when task explicitly needs benchmarks, competitions, public datasets.

Typical in this monorepo: rare. Prefer project docs + context7 first.

Degradation: skip + note N/A.

## mcp-files — surgical file ops

Prefer built-in `read/search/edit` first.

Use mcp-files when:
- exact byte offset insert required
- read specific symbol region with precision
- built-in tools cannot target location

Cursor: server `mcp-files` in `${HOME}/.cursor/mcp.json`.

## stitch — Google Stitch MCP

HTTP MCP: `https://stitch.googleapis.com/mcp`

**Prerequisite:** `stitch_api_key` via MCP inputs prompt (`${input:stitch_api_key}`).

If MCP shows **0 tools** — auth/key missing; ask user for API key, do not loop retries.

Use for: Stitch-native design/generation workflows when user explicitly requests Stitch.

Degradation: `[DEGRADED: stitch-unavailable]` → figma or manual UI implementation.

## Division vs forensics stack

| Need | Use |
|---|---|
| Known file or local question | Focused Read/search |
| Known symbol/flow with a structural gap | **CodeGraph** or **Octocode** → narrow Read; add the other only if needed |
| Unknown project scope after direct inspection | **tenets** → choose the smallest structural or Read follow-up |
| External library docs | **context7** |
| DB schema proof | **postgres** |
| Design file | **figma** / **stitch** |
| Orchestration reasoning | **crash** |
| Surgical file edit | **mcp-files** |
| Live provider app / platform health / review / webhooks console | dedicated provider skill (not this utility matrix) |

## Output Contract

- MCP(s) called + purpose
- Degradation tags if any
- No secrets in output

## Resources

- Forensics: `rkx-tenets`, `rkx-codegraph`, `octocode-code-forensics`
- UI: `browser-ui-evidence` and target-package UI skills
