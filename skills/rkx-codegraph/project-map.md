# Workspace — CodeGraph Project Map (portable template)

Index root: `${WORKSPACE_ROOT}`
Typical index size depends on the target workspace after excludes.

## Top-Level Layout (placeholders)

Replace these tokens with the target workspace layout after install:

```
<app-packages>/          # application packages (API, UI, workers, shared libs)
docs/                    # internal module docs (not treated as code logic)
${CONTROL_PLANE_ROOT}/   # Cursor agents, skills, commands, rules
```

Optional infrastructure roots when present in the target workspace:

```
<infra-runtime>/         # compose/runtime forensics only
<reverse-proxy>/         # reverse proxy config when applicable
```

## High-Value Query Zones

| Area | Portable pattern | What to query |
|------|------------------|---------------|
| HTTP/API entrypoints | `<app-packages>/**/*route*` / handler files | `kind=route`, domain noun |
| Services | `<app-packages>/**/services/**` | `*Service`, domain noun |
| Persistence models | `<app-packages>/**/entities/**` or ORM models | `*Entity` / model names |
| Background jobs | `<app-packages>/**/workers/**` | queue processors, `*Worker`, `*Job` |
| Migrations | `<app-packages>/**/migrations/**` | migration classes / SQL |
| Middleware | `<app-packages>/**/middleware/**` | auth, tenancy, request context |
| Primary UI | `<ui-package>/**` | pages, hooks (`use*`), API clients |

## Route Index Hints

CodeGraph may emit `route` nodes for HTTP handlers. Search by domain noun
(`provider`, `integration`, `workspace`, or the local equivalent) rather than
assuming fixed filenames from another repository.

Use `codegraph_search` with `--kind route` (CLI) or the equivalent MCP filter.

## Symbol Naming Patterns (typical)

- Models/entities: `*Entity` or project-local model suffix
- Routes/handlers: project-local `*.route.ts` / handler files
- Workers: `*Processor`, `*Queue`, coordinator helpers
- Migrations: timestamped classes implementing the local migration interface
- Frontend pages: under the primary UI package feature folders

## Excluded / Low-Trust Zones

Do not anchor architecture answers in:

- archival / export / tmp directories configured as out-of-scope for the workspace
- generated `dist/`, `node_modules/` (excluded from index)
- runtime storage artifacts

## Docs Cross-Reference

Internal docs: `${WORKSPACE_ROOT}/docs` when present.
After graph forensics, check docs for module-specific business rules before
implementing.

## Index Maintenance

```bash
codegraph status ${WORKSPACE_ROOT}
codegraph sync ${WORKSPACE_ROOT}          # after git pull / large merge
codegraph index ${WORKSPACE_ROOT} --force # rebuild if corrupted (rare)
```

Auto-sync runs via the MCP daemon during agent sessions when configured.
