# CodeGraph Recipes — workspace (graph+octocode)

Use these recipes only when a graph question exists. Start with the smallest
CodeGraph query that answers it. Add Octocode `lspGetSemantics` only when an
LSP precision gap remains; pass real `uri`, exact `symbolName`, and the
graph-provided `lineHint`.

## Architecture / Flow

### Background report sync (API → worker → DB)

**Context query:**
```
How does a report sync request flow from an API route through queue/worker to database persistence?
```

**Follow-up trace (example symbols — confirm via search first):**
```
codegraph_trace <routeHandlerSymbol> acquireSyncLease
```

**Files to expect:** `routes/provider*.route.ts`, `workers/**/sync*`, `syncCoordinator.ts`, report entities.

---

### Third-party message pipeline

**Context query:**
```
How does an inbound or outbound third-party message flow through server routes, services, and entities?
```

**Search seeds:** `integration`, `Integration`, route file `integration.route.ts`.

---

### Frontend page → backend API

**Context query:**
```
How does the frontend reports UI call the server API endpoints?
```

**Trace:** from page/hook symbol (e.g. `use*Report*`) toward a provider route handler.

---

### Subdomain / workspace tenancy

**Context query:**
```
How is workspace or subdomain context resolved from HTTP request to organization-scoped data access?
```

**Search seeds:** `subdomain`, `workspace`, middleware, `organization.route.ts`.

---

## Impact / Refactor

### Before editing shared sync coordinator

```bash
codegraph impact acquireSyncLease --depth 4
```

Summarize callers grouped by `workers/` vs `routes/` vs tests.

---

### Before changing an Entity field

1. `codegraph_search ReportEntity` (or target entity)
2. `codegraph_impact <EntityClassName>`
3. Check migration classes in same domain folder

---

### Before renaming an exported frontend hook

1. `codegraph_impact useReport*` within frontend scope
2. Cross-package: impact on server only if hook name appears in shared types (rare)

---

## Route Discovery

```bash
codegraph query "provider" --kind route --limit 20
codegraph query "integration" --kind route --limit 20
codegraph files ${WORKSPACE_ROOT} --filter "packages/server/src/routes/*"
```

---

## Worker / Queue Discovery

**Context query:**
```
What background workers and queue processors handle report synchronization and background sync?
```

**Search seeds:** `BullMQ`, `Queue`, `Worker`, `sync`, `backgroundSync`.

---

## Migration Forensics

**Context query:**
```
Which migrations touch the report table or related tables?
```

**Search seeds:** `report_table`, `MigrationInterface`, folder `database/migrations/postgres`.

---

## Quick Health / Session Start

```bash
codegraph status ${WORKSPACE_ROOT}
```

If pending files > 0 and task touches them → `codegraph sync` or targeted `Read`.

---

## MCP Call Sequence Templates (graph+octocode)

### Template A — "How does X work?" (default)

1. `codegraph_context` — full sentence task
2. `codegraph_explore` — top symbols only if bodies are needed
3. Add Octocode `lspGetSemantics(type="callHierarchy")` only for an LSP gap
4. Answer; `Read` only if staleness

### Template B — "What breaks if I change X?"

1. `codegraph_search` → `codegraph_impact`
2. Add Octocode `lspGetSemantics(type="references")` only when exact usages
   change the decision
3. Blast radius summary by package

### Template C — "Where is X?" (narrow)

1. `codegraph_search` → `codegraph_node`
2. Add Octocode `lspGetSemantics(type="references")` only when usages are
   part of the question
3. Stop (no grep)
