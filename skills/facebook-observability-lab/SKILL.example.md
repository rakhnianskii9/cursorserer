---
name: facebook-observability-lab
description: >-
  Use when tuning, benchmarking, or comparing the Facebook report-sync/background-sync
  observability loop: env-variable experiments, run-to-run comparison, unified markdown
  experiment ledger, pnpm logs evidence, speed, efficiency, stability, and change-quality
  measurement. For live Meta app rate limits / App Review / webhook console / Graph health
  via Meta Developer Tools MCP, pair with skill meta-developer-tools.
user-invocable: true
disable-model-invocation: false
---
# Facebook Observability Lab

Use this skill when the task is not just to fix one bug, but to run a disciplined control loop around the Facebook sync pipeline.

**Pair:** live Meta Developer App console (rate limits, App Review, compliance, webhook subscriptions) → skill `meta-developer-tools` (MCP `user-Meta Developer Tools`). This lab = sync pipeline experiments; that skill = live Meta app state.

This skill is for:
- env-profile experiments
- report sync vs background sync comparison
- observability run analysis
- fetch coverage and gap analysis
- stability tracking across repeated passes
- measuring the quality of code changes, not only runtime behavior
- writing one chat summary plus one unified markdown experiment ledger

Do not use this skill for generic Facebook CRUD work, unrelated UI changes, or one-off debugging without experiment tracking.

## Trigger Phrases

Load this skill when the user asks for any of the following:
- make the Facebook loading flow transparent
- compare runs / passes / env profiles
- benchmark report sync or background sync
- measure speed of statistics loading
- understand why one pass is faster or more stable than another
- store each iteration in one markdown table
- write evidence to logs and compare quality after fixes

## Scope Map

Primary backend paths:
- `packages/server/src/workers/reportSyncJob.ts`
- `packages/server/src/workers/facebookMarketingSyncJob.ts`
- `packages/server/src/enterprise/services/facebook-observability-run.service.ts`
- `packages/server/src/enterprise/services/facebook-insights-fetch-log.service.ts`
- `packages/server/src/enterprise/routes/fb-front.route.ts`
- `packages/server/src/services/facebook/FacebookMarketingService.ts`
- `packages/server/src/workers/helpers/envConfig.ts`

Primary documentation path:
- `docs/moduls/Facebook.md`

Primary runtime log artifact:
- `pnpm logs` -> `${CONTROL_PLANE_ROOT}/runtime/logs/README.md`

Primary code-reality files for reconciliation:
- `packages/server/src/enterprise/database/entities/*.ts` for table/entity ownership
- `packages/server/src/database/migrations/postgres/*.ts`
- `packages/server/src/workers/reportSyncJob.ts`
- `packages/server/src/workers/facebookMarketingSyncJob.ts`
- `packages/server/src/enterprise/services/facebook-observability-run.service.ts`
- `packages/server/src/enterprise/services/facebook-insights-fetch-log.service.ts`

## Source Of Truth Tables

These are the control-loop tables for this skill. Treat them as the authoritative storage for sync observability work.

| Table | Role in the loop | Primary writer | Primary reader |
|---|---|---|---|
| `workspace_facebook_config` | Workspace-level Facebook config and identity | config flows / admin services | workers, env/config checks |
| `facebook_sync_job` | Background sync job lifecycle and phase progress | background sync status services | operators, status endpoints |
| `facebook_ads_report` | Report-first sync state, selected scope, loaded ranges | fb-front report flows | report sync job, fb-front |
| `facebook_observability_run` | One run per significant pass with env snapshot and summaries | report/background workers | compare/detail/errors/gaps APIs |
| `facebook_insights_fetch_log` | Per-fetch audit trail: dates, outcomes, counters, errors, run binding | report/background workers | observability service, gap/error analysis |
| `facebook_ads_insight` | Cached insight rows used by UI and analytics | report/background workers | controllers, fb-front queries |
| `meta_insights_raw` | Raw import payloads for traceability and backfill analysis | report sync job | lower-level audits and raw verification |
| `facebook_daily_snapshot` | Derived daily entity baseline after full load | daily snapshot/report snapshot flows | timeline and diff logic |
| `facebook_entity_diff` | Entity deltas between snapshots | snapshot/diff flows | timeline and investigation |
| `facebook_learning_stage` | Learning-state timeline for ad sets | snapshot/diff flows | issue analysis and UI |
| `facebook_entity_issue` | Derived issue states opened/resolved over time | snapshot/diff flows | issue analysis and UI |

## Backend Flow Map

### Report-first path

1. `fb-front.route.ts` accepts report requests and sync-status reads.
2. `reportSyncJob.ts` creates `report_sync` or `report_extend` observability runs.
3. Fetch batches write into:
   - `facebook_insights_fetch_log`
   - `facebook_ads_insight`
   - `meta_insights_raw`
4. Report status is updated in `facebook_ads_report`.
5. Async report snapshot feeds summary back into `facebook_observability_run`.

### Background path

1. `facebookMarketingSyncJob.ts` starts a background-style observability run.
2. Per-account sync executes entities + insights + optional post-sync snapshot.
3. Fetch batches write into:
   - `facebook_insights_fetch_log`
   - `facebook_ads_insight`
4. Sync job metadata and phase progress write into `facebook_sync_job`.
5. Snapshot/diff stages update derived tables and the run summary.

### Read path

1. `facebook-observability-run.service.ts` builds list/detail/compare/errors/gaps views.
2. `fb-front.route.ts` exposes `/ads/observability/*` endpoints.
3. Operators or future UI use the run entity, fetch logs, errors, and gaps as the evidence layer.

## Code Reality Drift Reconciliation

If the actual codebase contradicts anything in this skill, the codebase wins.

Source-of-truth priority for drift resolution:

1. Current code in workers, services, entities, and migrations
2. Existing module documentation in `docs/moduls/Facebook.md`
3. This skill
4. Existing experiment-ledger text

Treat any mismatch between the skill and the code as `code reality drift`.

### Mandatory actions when drift is detected

1. Re-read the real writer/reader files before continuing.
   Minimum set:
   - `reportSyncJob.ts`
   - `facebookMarketingSyncJob.ts`
   - `facebook-observability-run.service.ts`
   - `facebook-insights-fetch-log.service.ts`
   - relevant entity/migration files for changed tables
2. Rebuild the effective table map and flow map from code, not from stale markdown.
3. Update the active ledger row with:
   - `Code Reality Drift = none | detected | fixed`
   - a short note of what was stale and which files corrected the understanding
4. If your own code changes caused the drift or resolved it, refresh all dependent evidence after the edits:
   - `get_errors`
   - filtered `pnpm build` only if the user explicitly requested build; otherwise explicit `N/A by policy`
   - `pnpm logs` when runtime paths were touched
   - observability run / fetch-log evidence for the new pass
5. Replace provisional metrics with post-fix metrics. Do not keep pre-fix numbers as the final verdict for the same iteration.
6. If table ownership, writers, readers, or route/service contracts changed materially, update the existing module documentation in `docs/moduls/Facebook.md` instead of creating a new markdown file.

### Post-change refresh rule

After any code edit that touches workers, services, routes, entities, or migrations in this module, the iteration is not complete until all of the following are refreshed:

- code-quality evidence
- runtime log artifact
- latest ledger row
- chat summary for that same iteration

## Required Workflow

1. Define one iteration goal.
   Example: compare `FACEBOOK_GRAPH_MAX_BATCH=20` vs `40` for report sync on the same report scope.
2. Freeze the comparison shape.
   Keep workspace, report scope, requested range, and trigger source stable unless the experiment explicitly changes them.
3. Capture the env profile truthfully.
   Only use typed readers:
   - `getFacebookEnvConfig()`
   - `getReportSyncConfig()`
4. Validate code reality before trusting the current flow map.
   If actual writers/readers/tables differ from this skill, run the drift-reconciliation protocol first.
5. Run or inspect exactly one iteration at a time.
6. Collect evidence from four layers:
   - current code reality for writers/readers/tables
   - run/fetch tables
   - logs via `pnpm logs`
   - code-change quality evidence if code was modified
7. Append exactly one row to the markdown experiment ledger for that iteration.
8. Return the same iteration summary in chat.
9. If the iteration included code changes, refresh build, editor-problem, log, and observability evidence after the edits before calling it better or worse.

## Mandatory Evidence Sources

Use these in order:

1. Code reality
   - current worker/service/entity/migration files for this module
   - `docs/moduls/Facebook.md` as the existing human-readable module contract
2. Observability tables and APIs
   - `facebook_observability_run`
   - `facebook_insights_fetch_log`
   - `/ads/observability/runs`
   - `/ads/observability/compare`
   - `/ads/observability/errors`
   - `/ads/observability/gaps`
3. Runtime logs
   - `pnpm logs`
   - generated artifact: `${CONTROL_PLANE_ROOT}/runtime/logs/README.md`
4. Code-quality evidence when code changed
   - `get_errors`
   - filtered `pnpm build` only if the user explicitly requested build; otherwise explicit `N/A by policy`
   - doc/schema note when applicable

Never claim runtime improvement from code alone. You need a run row and log evidence.
Never claim the documented flow is current until code reality has been checked after structural changes.

## Unified Markdown Ledger Contract

Maintain one markdown file for the active experiment set.

Default path:
- `plans/facebook-observability-lab.md`

Initialize it with:

```bash
bash ${CONTROL_PLANE_ROOT}/skills/facebook-observability-lab/scripts/init-report.sh
```

If the user wants a different path:

```bash
bash ${CONTROL_PLANE_ROOT}/skills/facebook-observability-lab/scripts/init-report.sh plans/custom-facebook-lab.md
```

The ledger MUST stay unified. Do not scatter one experiment across multiple markdown files unless the user explicitly asks for split ledgers.

Append one row per iteration with these minimum columns:

| Column | Meaning |
|---|---|
| `Iteration` | Sequential experiment/pass number |
| `Timestamp` | `${TZ}` time of recorded result (default `UTC`) |
| `Goal / Hypothesis` | What this pass tries to validate |
| `Env Profile` | Stable profile key or profile label |
| `ENV Delta` | Only the variables intentionally changed this pass |
| `Code Reality Drift` | `none`, `detected`, or `fixed`, with short drift note |
| `Run Kind` | `report_sync`, `report_extend`, `background_sync`, etc. |
| `Run / Scope` | Run id plus report id or sync job id |
| `Window` | Requested/effective date window or requested/effective days |
| `Result` | `success`, `partial`, `failed`, `cancelled` |
| `Speed` | Duration and throughput metrics |
| `Efficiency` | Fetch quality and usable-data efficiency |
| `Stability` | Error/gap/log-based stability verdict |
| `Change Quality` | Quality of code changes when code was touched |
| `Logs` | Log artifact path and key markers |
| `Notes / Next Step` | Main conclusion and next experiment |

## Metrics To Capture

Prefer raw metrics first. Only create a synthetic score if the user explicitly asks for scoring.

### Speed metrics

- `durationMs`
- `avgDurationMs`
- `maxDurationMs`
- `totalRowsReceived`
- `rowsPerSecond = totalRowsReceived / max(durationMs / 1000, 1)`

### Efficiency metrics

- `totalFetches`
- `successFetches`
- `partialFetches`
- `failedFetches`
- `rowsInserted`
- `rowsUpdated`
- `rowsSkipped`
- `fetchSuccessRatio = successFetches / max(totalFetches, 1)`
- `usableDataReached = yes/no`

### Stability metrics

- `totalErrorCount`
- gap count from `getGaps()` or DB evidence
- presence of root failure stage in `errorSummary`
- repeated worker exceptions in `${CONTROL_PLANE_ROOT}/runtime/logs/README.md`
- verdict:
  - `PASS` when terminal result is `success`, gaps are zero or accepted, and logs show no repeating runtime fault
  - `WARN` when result is `partial` or logs show recoverable errors
  - `FAIL` when result is `failed`, gaps are material, or runtime logs show recurring faults

### Change-quality metrics

Only for iterations that included code changes:

- build result for touched package(s) only if the user explicitly requested build
- editor problems count after edits
- docs updated: `yes/no`
- schema/migration note: `approved-and-handled | deferred-by-policy | N/A`
- rollback note present: `yes/no/N/A`
- verdict:
   - `PASS` when the allowed validation evidence is present, editor problems are clean, and required docs/schema notes are handled
  - `WARN` when behavior improved but validation is incomplete
  - `FAIL` when build or correctness evidence is missing

If the iteration is data-only and no code changed, write `Change Quality = N/A (no code change)`.

### Code-reality drift metric

- `none` when the skill's current table/flow assumptions matched the inspected code
- `detected` when inspected code contradicted the skill or ledger assumptions for this iteration
- `fixed` when code or documentation was updated and the final ledger/chat summary reflects the corrected structure

If drift was detected, record the exact files that re-established the truth.

## Logging Contract

For every benchmark or tuning iteration:

1. Refresh logs with:

```bash
pnpm logs
```

2. Treat `${CONTROL_PLANE_ROOT}/runtime/logs/README.md` as the canonical collected runtime artifact for that iteration.
3. In the chat answer and markdown row, reference the exact log markers that support the verdict.
4. If code is changed in workers/services/routes, keep structured logger fields such as:
   - `workspaceId`
   - `reportId`
   - `syncJobId`
   - `observabilityRunId`
   - `accountId`
   - `runKind`
5. Do not claim log evidence unless `pnpm logs` was refreshed during the current iteration.

## Chat Output Contract

Every use of this skill must return:

1. A short summary paragraph.
2. The latest iteration row rendered in chat as a compact table or flat metric list.
3. A verdict block with:
   - code reality drift
   - speed
   - efficiency
   - stability
   - change quality
4. The next most useful variable or hypothesis to test.

## Guardrails

- Do not fabricate metrics that are absent from DB, API, or logs.
- Do not keep stale table or flow descriptions when current code disproves them.
- Do not compare runs with different scopes and then present that as a pure env comparison.
- Do not use full `process.env` snapshots; only allowlisted typed config readers.
- Do not claim build evidence unless the user explicitly requested build; otherwise record `N/A by policy` and rely on other allowed evidence.
- Do not skip post-edit evidence refresh after changing worker/service/route/entity/migration files.
- Do not write more than one experiment ledger unless the user explicitly asks for multiple ledgers.
- Do not replace raw evidence with a subjective story. The markdown row must stay evidence-first.