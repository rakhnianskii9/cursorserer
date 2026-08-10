# CodeGraph Recipes — portable workspace (graph+octocode)

Use these recipes only when a graph question exists. Start with the smallest
CodeGraph query that answers it. Add Octocode `lspGetSemantics` only when an
LSP precision gap remains; pass real `uri`, exact `symbolName`, and the
graph-provided `lineHint`.

Replace placeholder symbols/paths with names discovered in the target workspace.

## Architecture / Flow

### API → worker → persistence

**Context query:**
```
How does a background job request flow from an API route through queue/worker to persistence?
```

**Follow-up trace (confirm symbols via search first):**
```
codegraph_trace <routeHandlerSymbol> <coordinatorOrProcessorSymbol>
```

**Files to expect:** route/handler files, worker/queue modules, persistence models.

---

### Inbound/outbound integration pipeline

**Context query:**
```
How does an inbound or outbound integration message flow through routes, services, and persistence?
```

**Search seeds:** integration domain nouns and the local route/handler naming pattern.

---

### Frontend page → backend API

**Context query:**
```
How does a UI page or hook call the server API endpoints?
```

**Trace:** from page/hook symbol toward a route/handler symbol.

---

### Tenant / workspace request context

**Context query:**
```
How is workspace or tenant context resolved from an HTTP request to scoped data access?
```

**Search seeds:** middleware, workspace/tenant helpers, organization/account routes.

---

## Impact / Refactor

### Before editing a shared coordinator

```bash
codegraph impact <sharedCoordinatorSymbol> --depth 4
```

Summarize callers grouped by workers vs routes vs tests.

---

### Before changing a persistence model field

1. `codegraph_search <ModelOrEntityName>`
2. `codegraph_impact <ModelOrEntityName>`
3. Check migration classes in the same domain folder

---

### Before renaming an exported UI hook

1. `codegraph_impact <hookName>` within the UI package scope
2. Cross-package impact only if the name appears in shared types

---

## Route Discovery

```bash
codegraph query "<domain-noun>" --kind route --limit 20
codegraph files ${WORKSPACE_ROOT} --filter "<app-packages>/**/*route*"
```

---

## Worker / Queue Discovery

**Context query:**
```
What background workers and queue processors handle the target synchronization or job domain?
```

Search seeds: `Worker`, `Processor`, `Queue`, domain nouns from the task.

---

## Octocode precision add-on

Use only after CodeGraph names a concrete symbol and file:

```text
lspGetSemantics:
  type: references | callHierarchy
  uri: <file uri from graph>
  symbolName: <exact symbol>
  lineHint: <graph line>
```
