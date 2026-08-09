---
name: docker-diagnostics
description: 'Use when backend/runtime/container health must be verified with evidence: Docker CLI status, logs, compose services, collector bundle, and post-change runtime checks without rebuilding images.'
user-invocable: true
disable-model-invocation: false
---

# Docker Diagnostics Skill

**Domain:** Runtime diagnostics via Docker CLI (containers, logs, compose services)
**Scope:** Evidence-first runtime health checks for deployment, service failures, and post-implementation validation
**Tool:** Docker CLI (`docker`, `docker-compose`) via terminal
**Preferred collector:** `${WORKSPACE_ROOT}/scripts/pnpm/collect-logs.sh`

Used by **RKX-Loop** validate phases and **rkx-loop-core** forensics when runtime evidence is required.

---

## When to Use (Triggers)

Invoke this skill when:
- 🔴 **Bug fix**: user reports a specific runtime failure (500 errors, service down, queue stuck)
- 🔴 **Implementation phase complete**: after code changes that touch server/worker/queue/db
- 🟡 **Code review / validate(diff)**: validating that changes didn't break running services
- 🟡 **Performance issue**: slow response, memory leak, CPU spike
- 🟡 **Deployment validation**: after a non-Docker build, service restart, or other runtime-affecting validation step
- ⚪ **Risk assessment**: assessing runtime risk of proposed changes

**Important:**
- Never require or suggest Docker image rebuild as part of this skill. Use read-only Docker CLI evidence and container/runtime checks only.
- **Docker compose rebuild** (`pnpm build:compose`, `docker compose build`, etc.) is allowed **only** after the RKX-Loop gate: the USER says `Ship` or `Build docker` and validate(diff) is green. See `${CONTROL_PLANE_ROOT}/rules/infrastructure-core.mdc` and `${CONTROL_PLANE_ROOT}/rules/rkx-always-on.mdc`.

**NOT for:**
- Static code analysis (use **graph+octocode** pair: `rkx-codegraph` + `octocode-code-forensics`)
- UI-only changes with no backend impact (use `browser-ui-evidence` / built-in Browser Tab on `cd ${WORKSPACE_ROOT}/frontend && pnpm dev`)
- Documentation-only updates

## Output Contract

Return:
- collection path used: collector or manual fallback
- artifact path when produced
- container health summary
- key error lines or explicit clean result
- follow-up recommendation: none | deeper drill-down needed | rollback discussion required

---

## Preferred Execution Path

If available, prefer the project collector script:

```bash
bash ${WORKSPACE_ROOT}/scripts/pnpm/collect-logs.sh
```

What it collects into `${CONTROL_PLANE_ROOT}/runtime/logs/README.md`:
- docker logs for: `web`, `api`, `worker`, `db`, `cache`
- `redis-cli INFO`
- latest `/runtime/logs/server.log.*` tail when present

Use this script as the default runtime-evidence bundle for:
- L1 forensic triage (`/loop-bug`, rkx-loop-validate)
- L2 post-implementation validation (`/loop-implement`, validate(diff))
- Runtime gate in review / devil-advocate phases inside RKX-Loop

Fallback policy:
- If the script is missing, fails, or deeper targeted inspection is needed, fall back to the manual protocol below.
- Do not edit the script from an agent unless the user explicitly asked to change diagnostics tooling.

Recommended evidence handoff:
```markdown
### Docker Diagnostics Bundle
- Collector: `bash ${WORKSPACE_ROOT}/scripts/pnpm/collect-logs.sh`
- Artifact: `${CONTROL_PLANE_ROOT}/runtime/logs/README.md`
- Result: {success | partial | failed}
- Follow-up: {none | manual container drill-down required}
```

Handoff rule:
- When the preferred collector is used, the phase handoff MUST explicitly reference `${CONTROL_PLANE_ROOT}/runtime/logs/README.md` as the evidence artifact.
- If the artifact was not produced, state why and switch to manual evidence collection explicitly.

---

## Evidence Collection Protocol

### Phase 1: Container Health Check (ALWAYS first)

Preferred path:

```bash
bash ${WORKSPACE_ROOT}/scripts/pnpm/collect-logs.sh
```

Manual fallback:

```bash
# 1. Check all project containers status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Check for recently stopped/failed containers
docker ps -a --filter "status=exited" --format "table {{.Names}}\t{{.Status}}\t{{.ExitCode}}"
```

**Expected output:**
- `api`: Up (healthy)
- `worker`: Up (healthy)
- `db`: Up (healthy)
- `cache`: Up (healthy)

**Evidence format:**
```markdown
### Container Health
- api: {UP | DOWN | RESTARTING} (uptime: {duration})
- worker: {UP | DOWN | RESTARTING} (uptime: {duration})
- db: {UP | DOWN | RESTARTING} (uptime: {duration})
- cache: {UP | DOWN | RESTARTING} (uptime: {duration})
```

### Phase 2: Logs Diagnosis (when Phase 1 shows issues OR task involves runtime bug)

Preferred path:

```bash
bash ${WORKSPACE_ROOT}/scripts/pnpm/collect-logs.sh
# then inspect ${CONTROL_PLANE_ROOT}/runtime/logs/README.md
```

Manual fallback:

```bash
# 3. Check API logs (last 50 lines + errors)
docker logs api --tail 50 2>&1 | grep -E "ERROR|WARN|FATAL|Exception|failed"

# 4. Check worker logs (last 50 lines + errors)
docker logs worker --tail 50 2>&1 | grep -E "ERROR|WARN|FATAL|Exception|failed"

# 5. Check database logs (last 30 lines + errors)
docker logs db --tail 30 2>&1 | grep -E "ERROR|FATAL|connection refused"

# 6. Check cache logs (last 20 lines)
docker logs cache --tail 20
```

**Evidence format:**
```markdown
### Logs Snapshot (last 50 lines each)
**api errors:**
{paste ERROR/WARN lines or "No errors"}

**worker errors:**
{paste ERROR/WARN lines or "No errors"}

**db errors:**
{paste ERROR/FATAL lines or "No errors"}

**cache status:**
{paste relevant lines or "Healthy"}
```

### Phase 3: Compose Services Status (when compose-level changes made)

```bash
# 7. Check docker-compose services
cd ${WORKSPACE_ROOT}/docker && docker-compose ps

# 8. Check compose logs (aggregated)
cd ${WORKSPACE_ROOT}/docker && docker-compose logs --tail=30 --timestamps
```

---

## Integration Points (RKX-Loop)

### L1 forensic (`/loop-bug`, rkx-loop-validate plan)
**When:** User reports a runtime bug
**Steps:**
1. Prefer `bash ${WORKSPACE_ROOT}/scripts/pnpm/collect-logs.sh`
2. If issues found → run Phase 2 (logs diagnosis)
3. Include evidence in findings → handoff to RKX-Loop phase ledger

### L2 implement (`/loop-implement`, validate(diff))
**When:** Phase involves server/worker/queue/db changes
**Steps:**
1. After code changes + build → prefer `bash ${WORKSPACE_ROOT}/scripts/pnpm/collect-logs.sh`
2. If Phase 1 shows restarts/failures → run Phase 2
3. Include evidence in validate(diff) output

### Runtime validation gate
**When:** Review / validate for server/backend/db changes
**Steps:**
1. Prefer collector script — **mandatory** for backend changes
2. If any container DOWN or recent restarts → FAIL validation (needs revision)
3. If Phase 1 clean → check Phase 2 logs for new ERROR/WARN patterns
4. Reference `${CONTROL_PLANE_ROOT}/runtime/logs/README.md` when collector path was used

### Risk assessment (high-risk scope)
**When:** DB schema, auth, payments, infra
**Steps:**
1. Prefer collector for baseline health evidence
2. If proposing changes → identify rollback commands
3. Include rollback plan in validate output

---

## Rollback Detection (CRITICAL for bug fixes)

If container health check shows failures AFTER implementation:

**Immediate rollback triggers:**
- Any container stuck in `Restarting` loop
- `db` or `cache` down (data layer failure)
- `api` exit code != 0 (server crash)

**Rollback commands (copy-ready):**
```bash
# 1. Stop current containers
cd ${WORKSPACE_ROOT}/docker && docker-compose down

# 2. Verify git status (staged changes)
cd ${WORKSPACE_ROOT} && git status

# 3. STOP — DO NOT proceed with git rollback without user confirmation
# Report failure + rollback proposal to user
```

**NEVER execute git rollback commands (`git reset`, `git restore`, `git checkout`) without user verification** (per code-rules.instructions.md).

---

## Example Evidence Block (for RKX-Loop handoff)

```markdown
## Docker Diagnostics Evidence

**Trigger:** validate(diff) after server/Entity changes

**Phase 1: Container Health**
- service-main: UP (uptime: 2h 15m)
- service-worker: UP (uptime: 2h 15m)
- service-postgres: UP (uptime: 5h 32m)
- service-redis: UP (uptime: 5h 32m)

**Phase 2: Logs Snapshot (last 50 lines)**
- service-main errors: No errors
- service-worker errors: No errors
- service-postgres errors: No errors
- service-redis status: Healthy

**Verdict:** ✅ No runtime issues detected post-implementation

**Tools used:** `docker ps`, `docker logs api`, `docker logs worker`
```

Or, when using the preferred collector:

```markdown
## Docker Diagnostics Evidence

**Trigger:** Runtime triage / post-implementation validation

**Collector:** `bash ${WORKSPACE_ROOT}/scripts/pnpm/collect-logs.sh`
**Artifact:** `${CONTROL_PLANE_ROOT}/runtime/logs/README.md`

**Bundle contents:**
- Container logs: web, api, worker, db, cache
- Redis INFO
- Latest `/runtime/logs/server.log.*` tail (if present)

**Verdict:** {✅ evidence collected | ⚠ partial | ❌ failed}
```

---

## Maintenance Notes

- Keep the preferred collector path in sync with `${WORKSPACE_ROOT}/scripts/pnpm/collect-logs.sh`
- If new services added (e.g., `service-nginx`, `service-queue`) → update Phase 1 checklist
- If the collector script adds/removes services, update the evidence description in this skill
- If docker-compose.yml location changes → update commands
- Log retention: docker keeps last 1000 lines by default; for deeper history use project logs in `.service/storage/logs/` (if exists)

---

**Last Updated:** 2026-07-23
**Used by:** RKX-Loop + rkx-loop-validate / rkx-loop-implement phases
**Dependencies:** Docker CLI, docker-compose
