# Workspace — CodeGraph Project Map

Index root: `${WORKSPACE_ROOT}`
Typical index size: a few thousand files and tens of thousands of nodes.

## Top-Level Layout

```
packages/
  server/           # application API, workers, ORM, migrations
  components/       # application component packages
  frontend/         # primary frontend UI
  admin-ui/         # administrative UI
  messaging/
    builder/        # messaging builder
    chat/           # messaging chat
    portal/         # messaging portal
docker/             # compose/runtime (infra forensics only)
nginx/              # reverse proxy
docs/               # internal module docs (not indexed as code logic)
${CONTROL_PLANE_ROOT}/            # Cursor agents, skills, commands, rules
```

## Server — High-Value Paths

| Area | Path pattern | What to query |
|------|--------------|---------------|
| Application routes | `packages/server/src/routes/*.route.ts` | `kind=route`, file name (`provider`, `integration`, `workspace`) |
| Services | `packages/server/src/**/services/**` | `*Service`, domain noun |
| Entities | `packages/server/src/**/entities/**` | `*Entity`, table-related names |
| Workers | `packages/server/src/workers/**` | queue processors, `*Worker`, `*Job` |
| Background sync | `packages/server/src/workers/**/sync*` | `SyncCoordinator`, `acquireSyncLease`, `report` |
| Migrations | `packages/server/src/database/migrations/postgres/` | `MigrationInterface` classes |
| Middleware | `packages/server/src/**/middleware/**` | auth, tenancy, subdomain |

## Route Index Hints

CodeGraph emits `route` nodes for Express-style handlers. Common entry files:

- `provider.route.ts` — external accounts, disconnect, provider bridge
- `integration.route.ts` — third-party integration endpoints
- `workspace.route.ts`, `organization.route.ts`, `user.route.ts` — tenancy

Use `codegraph_search` with `--kind route` (CLI) or the equivalent MCP filter.

## Frontend Surfaces

| Package | Stack | Typical symbols |
|---------|-------|-----------------|
| `frontend` | React, Vite, Tailwind | page components, hooks (`use*`), API modules |
| `admin-ui` | React, admin UI library | views, stores, forms |
| `messaging/*` | React per module | builder/chat/portal-specific routes and stores |

Cross-boundary traces often stop at HTTP client calls; continue on server route
nodes.

## Symbol Naming Patterns

- Entities: `*Entity`, file `*.entity.ts`
- Routes: Express handlers in `*.route.ts`, graph kind `route`
- Workers: `*Processor`, `*Queue`, coordinator helpers in `workers/helpers/`
- Migrations: timestamp prefix, class implements `MigrationInterface`
- Frontend pages: under `packages/frontend/src/pages/` or feature folders

## Excluded / Low-Trust Zones

Do not anchor architecture answers in:

- `x-old-projects/`
- `user-export/`, `code-export/`, `tmp/`
- `.service/storage/` runtime artifacts
- generated `dist/`, `node_modules/` (excluded from index)

## Docs Cross-Reference

Internal docs: `${WORKSPACE_ROOT}/docs`
After graph forensics, check docs for module-specific business rules before
implementing.

## Index Maintenance

```bash
codegraph status ${WORKSPACE_ROOT}
codegraph sync ${WORKSPACE_ROOT}          # after git pull / large merge
codegraph index ${WORKSPACE_ROOT} --force # rebuild if corrupted (rare)
```

Auto-sync runs via the MCP daemon during agent sessions.
