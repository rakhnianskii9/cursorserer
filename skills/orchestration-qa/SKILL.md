---
name: orchestration-qa
description: 'Use when validating Cursor workspace orchestration and control-plane files: agents, skills, commands, rules, MCP config, CURSOR-UX.md, loops artifacts, model bindings, canonical paths, and legacy trace cleanup.'
user-invocable: true
disable-model-invocation: false
---
# Orchestration QA Skill

Use this skill when validating that Cursor workspace orchestration is configured and functioning.

Trigger: changes to `${CONTROL_PLANE_ROOT}/agents|skills|commands|rules`, Cursor MCP configs, `${CONTROL_PLANE_ROOT}/CURSOR-UX.md`, or `loops/`.

Goal: validate the active Cursor (`CONTROL_PLANE_ROOT`) RKX-Loop control plane. Catch structural breakage, stale paths, false summaries, doctrine drift, and script/artifact mismatches.

## Validation Checklist

### 1. Agent Files (`${CONTROL_PLANE_ROOT}/agents/*.md`)
- [ ] Every agent file has syntactically valid YAML frontmatter; do not require fields Cursor does not require
- [ ] Agent frontmatter declares only capabilities relevant to the role; omitted optional fields are valid
- [ ] If declared, `tools` references only tools available in Cursor
- [ ] `${CONTROL_PLANE_ROOT}/agents/rkx-loop.md` is the single active orchestrator; no legacy agent zoo is restored
- [ ] If declared, `skills` matches directories actually present under `${CONTROL_PLANE_ROOT}/skills`
- [ ] If declared, `mcpServers` matches servers configured in the Cursor runtime
- [ ] Hard guardrail against `git reset/restore/clean` present in every agent with write tools
- [ ] Read-only roles explicitly set `readonly: true` and do not authorize edits in their bodies
- [ ] Discovery surface quality: `description` is specific enough for agent selection and contains realistic trigger terms for the role
- [ ] Tool-contract compliance: body text does not mandate nonexistent tool namespaces or unavailable MCP/tool names

### 2. RKX-Loop Orchestration (not zoo)
- [ ] `${CONTROL_PLANE_ROOT}/agents/rkx-loop.md` references active Cursor skills, `${CONTROL_PLANE_ROOT}/CURSOR-UX.md` / loop rules (`infrastructure-core`, `rkx-always-on`)
- [ ] No orphan legacy orchestrator agents or duplicate active roles are required
  in the active control plane
- [ ] Escalate stubs (if any) live under explicit `escalate/` — not restored as default workflow
- [ ] L1/L2 gate lexicon consistent between `infrastructure-core.mdc` / `rkx-always-on.mdc`, RKX-Loop agent, and loop skills
- [ ] Independent checker slots fan out in one concurrent batch; `merger` is a single join barrier and is not dispatched once per slot
- [ ] Bootstrap Merger returns a WaveSpec (`BOOTSTRAP_WAVE_SPEC`); post-wave
  Merger emits a Proposal then, after Advocate, an AcceptedDecision
  `NEXT_WAVE_SPEC`, `END`, or `HARD_BLOCKER`. Orchestrator executes only a
  `ControllerAction` and writes zero files
- [ ] `${CONTROL_PLANE_ROOT}/agents/devil.md` exists: readonly, the verified Advocate model / `__MODEL_ADVOCATE__`, `AdvocatePacket` contract; no `loops/**` writes; no END decision; no slot spawn
- [ ] Advocate runs once per `proposal_id` (`CLEAN`|`HOLE`). Material HOLE is
  not an AcceptedDecision. `decision_id` appears only after settlement.
  Bootstrap and slots do not invoke Advocate. Boss is checkpoint-only at
  waves 10/20
- [ ] `HARD_BLOCKER` gets at most one `BLOCKER_RECOVERY` per `proposal_id`
  (forbidden at wave 20 / after checkpoint 20). No Merger⇄Advocate chat loop
- [ ] POST_WAVE NEXT at wave 10/20 authorizes Boss checkpoint evaluation, not
  dispatch of wave N+1. Wave 21 is forbidden
- [ ] Each slot packet is persisted under
  `loops/<run>/wave-<n>/slots/<slot-id>/attempts/<attempt-id>/report.md`
  before Merger join
- [ ] Each new slot packet and synthesis/Advocate artifact records the factually selected `MODEL`; missing legacy model data is disclosed as unrecorded rather than inferred from role binding
- [ ] Root-depth gate uses the canonical four questions and is not replaced by an invented questionnaire
- [ ] `WAVE_SPEC` schema v1 carries `spec_revision`, `token_mode` (`API|CURSOR`),
  the paired billing/credential scope (`API_CREDENTIALS|CURSOR_SUBSCRIPTION`) without values,
  hypotheses, one expected fact and expected decision change per slot,
  `REQUIRED|OPTIONAL` slot semantics, correlation/searchability contracts,
  parallel dispatch/join, `max_slot_attempts`, artifact references, and stop
  condition. `decision_kind` is not canonical
- [ ] Merger writes revisioned `wave-<n>/preflights/<revision_seq>.yaml`.
  Capability observation is `READY|UNAVAILABLE|STALE|INVALID`. PreflightDecision
  is `DISPATCH|REPLAN|WAITING_USER|HARD_BLOCKER_CANDIDATE`. Only READY required
  slots dispatch
- [ ] `BLUEPRINT-SCOUT` routes to the token-mode-specific read-only Scout,
  carries an explicit `CATALOG_ID`, and reads only the registry, selected
  catalog index, and exact pinned local source refs; selection follows the
  registry `domain_routes`
- [ ] Blueprint candidates have stable ids, catalog revision, source refs,
  catalog id, reference type, reference applicability, relation, verification
  targets, and confidence basis; legacy blueprint applicability is only a
  matching alias
- [ ] Blueprint `qualified_pairs` pass relevance/applicability, causal relation,
  verifiable target, and root/plan/confidence impact predicates before dispatch
- [ ] `coverage_decision` is `REQUIRED`, `OPTIONAL`, or `NOT_NEEDED` after
  merge; `coverage_required` is derived and never an unsupported free boolean
- [ ] Coverage dispatches only qualified pairs, declares a budget, records
  overflow handling, and never silently drops a pair
- [ ] Every confidence field is a `0%`–`100%` percentage with `CONFIDENCE_BASIS`; no qualitative, decimal, or missing values remain
- [ ] Chat summary ALWAYS is restored in `rkx-loop-core` (5 parts + `chat_itog_delivered`) and referenced by orchestrator/commands/rules; `loops/<run>/` is not a chat substitute
- [ ] Part 5 follows the `rkx-loop-core` binding: arbitrary-length causal chain, business/UI translation, bold `Basis`/`Where` labels with italic bodies, exact percentages, evidence ids, and factual model attribution or explicit role-binding disclosure
- [ ] Slack lifecycle notifications use the exact event
  `loops/<run>/deliveries/<event_id>/lifecycle.json` with
  `conversation_id`/`event_id` correlation from `state/current.yaml`, preserve
  `problem_title`, and do not select artifacts by mtime
- [ ] Slack ownership is split: stop-hook sends the lifecycle card; MCP sends
  at most one full verdict only after `chat_itog_delivered`; missing artifacts,
  mismatched conversations, and transport failures are fail-open
- [ ] 17 molecules are present in `rkx-loop-core`; molecule 2 binds Part 5 Verdict; molecule 12 binds ASCII; molecule 3 uses wave protocol without unconditional `N≥3`
- [ ] Legacy `${CONTROL_PLANE_ROOT}/prompts/loop-*.md` do not reintroduce Swarm `N≥3` / findings-5-col-without-Chat-summary drift against commands

### 3. Skills (surface-specific SoT)
- [ ] Every enabled skill directory contains a materialized `SKILL.md` file
- [ ] Materialized SKILL.md has valid frontmatter: `name`, `description`
- [ ] `rkx-loop-*` skills referenced by commands actually exist
- [ ] Enabled generic skills are present: evidence routing, code review,
  security, browser evidence, diagnostics, and any explicitly selected MCP
  integration
- [ ] Skill descriptions contain trigger phrases strong enough for discovery
- [ ] Skill scope matches the file type: workflow bundle vs always-on rule vs loop phase responsibility is not confused
- [ ] Cursor skills treat `${CONTROL_PLANE_ROOT}/` as their control plane and do not treat `.github/` as active control plane

### 4. Commands (`${CONTROL_PLANE_ROOT}/commands/loop-*.md`)
- [ ] Each `/loop-*` command loads the matching `rkx-loop-*` skill or thin launcher body
- [ ] Commands use valid Cursor invocation and delegation surfaces
- [ ] No prod credentials or passwords in command bodies

### 5. MCP Servers (workspace `${CONTROL_PLANE_ROOT}/mcp.json`, optional user `${HOME}/.cursor/mcp.json`)
- [ ] JSON is valid and parseable
- [ ] Required MCP servers are present in the Cursor runtime being validated
- [ ] Every MCP used by active rules, skills, or agents exists in the current runtime or is explicitly degraded; registered but unused MCPs are not advertised as workflow requirements
- [ ] Meta Developer Tools is routed by `meta-developer-tools` when configured in the Cursor runtime
- [ ] Every MCP server referenced in agent `mcpServers` / skills exists in Cursor's MCP config or is explicitly documented as unavailable
- [ ] No hardcoded secrets in mcp.json; use `${env:...}` / OAuth / prompt inputs
- [ ] Workspace MCP may use `${workspaceFolder}` / `${userHome}`; user-level
  MCP should use resolved local paths or `${userHome}`
- [ ] Control-plane summaries are truthful: MCP servers claimed in rules or skills actually exist in Cursor's mcp.json or are labeled unavailable
- [ ] No stale platform claims: removed or never-configured servers are not advertised as available
- [ ] Project SoT is `${CONTROL_PLANE_ROOT}/mcp.json`; `${HOME}/.cursor/mcp.json`
  is a personal overlay only; `.vscode/mcp.json` is not canonical

### 6. Rules (`${CONTROL_PLANE_ROOT}/rules/*.mdc`)
- [ ] Rules have valid frontmatter when their format requires it
- [ ] `rkx-always-on.mdc` and `token-economy.mdc` exist with the current Cursor control-plane map
- [ ] Rules do not contradict `${CONTROL_PLANE_ROOT}/CURSOR-UX.md` or gate lexicon in `infrastructure-core.mdc` / `rkx-always-on.mdc`
- [ ] `token-economy.mdc` makes compact artifact/delta handoffs and gap-driven MCP routing always-on without forcing a loop
- [ ] Guard content matches doctrine: no rm -rf, no git reset/restore/clean, no unauthorized build/migration/docker mutation

### 7. Loops artifacts (`loops/`)
- [ ] `loops/README.md`, `_models.md`, `_registry.md`, `_decisions/` committed; run folders gitignored
- [ ] `_models.md` slot → runtime mapping is consistent with skills referencing slot ids
- [ ] ADR-001 documents single orchestrator (no zoo restore)
- [ ] The materialized `RUN.md` template uses only `ide | auto` mode values

### 8. Operational Orchestration Artifacts
- [ ] `scripts/validate-rkx-loops.sh` checks the active Cursor control plane and passes
- [ ] `scripts/validate-rkx-blueprint-coverage.py` passes both qualification-only
  and `--require-results` validation for blueprint artifacts
- [ ] The reference registry and telephony catalog pass schema validation:
  unique ids, known catalog/source ids, local source notes, pinned revisions,
  and allowed reference types/targets
- [ ] Active artifacts use built-in todo tracking or `loops/<run>/` ledgers for task tracking
- [ ] `${CONTROL_PLANE_ROOT}/CURSOR-UX.md` matches actual paths and gate lexicon

### 9. Cross-File Consistency
- [ ] `${CONTROL_PLANE_ROOT}/CURSOR-UX.md` exists, maps the Cursor `${CONTROL_PLANE_ROOT}/*` surface, and lists the active orchestrator / slash entry points
- [ ] Skill routing in Cursor RKX-Loop and loop skills matches actual Cursor skills
- [ ] Canonical paths are correct everywhere: no stale active references to root `AGENTS.md`, `${CONTROL_PLANE_ROOT}/rules/browser-builtin-only.mdc`, `.github/skills/*`, `.vscode/RKX-LOOPS.md`, or `*.prompt.md` as required SoT
- [ ] Registry summaries do not claim capabilities absent from actual config (for example MCP families, scripts, or legacy zoo agents)

### 10. Orchestration Doctrine Consistency
- [ ] Startup protocol is consistent across rules and RKX-Loop: smallest direct inspection → gap-driven routing → Crash framing only when used
- [ ] Durable memory is consistently stored as compact cited loop artifacts/living-plan state; no absent Memory MCP is advertised
- [ ] Solve-loop / completion doctrine is explicit in RKX-Loop and does not contradict always-on rules
- [ ] Gate lexicon (`implementation_authorized` plus later `Smash`/`Build`/`Ship` vs `Build docker`) consistent everywhere
- [ ] MCP degradation-tag policy is consistent across orchestration files
- [ ] **Forensic routing** is gap-driven in every active source: focused Read/search first; Tenets only for unknown scope; CodeGraph or Octocode only for a structural gap; Postgres conditional; Crash cross-cutting synthesis. This is consistent across rules and skills
- [ ] Always-fast discipline (mode=fast by default, full-repo not balanced, ≤6 parallel `rank_files`, no rank∥codegraph batch) is consistent across SKILL/project-tenets/rules
- [ ] Build/migration/docker-mutation prohibitions and allowed read-only validation paths are consistent across rules, RKX-Loop, and `infrastructure-core.mdc` / `rkx-always-on.mdc`
- [ ] Browser policy: built-in browser-use MCP only; dual-track fast/clean documented in `browser-ui-evidence` and `rkx-loop-front`

### 11. Legacy Trace Hygiene
- [ ] Active Cursor control-plane files reference only their current mechanisms (RKX-Loop, loop commands, loops runs)
- [ ] Archive data (`.github`, `.vscode/RKX-LOOPS.md`) may preserve history, but active docs/scripts/skills must not instruct agents to read or restore it; `CONTROL_PLANE_ROOT` is active Cursor control plane
- [ ] No stale examples require an external transport or an obsolete agent zoo

### 12. Model Naming (AI Naming Policy)
- [ ] Verify each declared agent model or runtime alias in the actual Cursor picker/runtime; repository text alone cannot prove availability
- [ ] Repository checks may validate `${CONTROL_PLANE_ROOT}/CURSOR-MODELS.md` and declared bindings for consistency only; they cannot validate runtime availability
- [ ] Do not hardcode an unapproved API-key binding; report model availability only from the actual Cursor runtime/picker

### 13. Review Method
- [ ] Validate syntax first, then RKX-Loop hierarchy, then cross-file truthfulness, then doctrine, then legacy-trace hygiene
- [ ] Prefer findings ordered by severity: CRITICAL → WARNING → INFO
- [ ] Treat code/config reality as source of truth over markdown summaries when they conflict
- [ ] If a summary table and runtime config disagree, report the summary as false rather than assuming intent

## Output Format

```markdown
## Orchestration QA Report

| # | Severity | Check | Status | File | Issue | Fix |
|---|----------|-------|--------|------|-------|-----|
| 1 | CRITICAL/WARNING/INFO | Agent frontmatter | PASS/FAIL | path | detail | action |
| ... | ... | ... | ... | ... | ... |

**Summary**: X/Y checks passed. {PASS | FAIL — N critical issues}

**Truthfulness Gaps**
- List every place where docs/registry/skill text claims a capability that the actual control plane does not provide.

**Doctrine Gaps**
- List mismatches in startup protocol, memory lifecycle, solve-loop, gate lexicon, diagnostics, or degradation-tag policy.

**Legacy Trace Gaps**
- List any non-current mechanism still referenced in active Cursor files.
```

## Severity Levels
- **CRITICAL**: RKX-Loop won't load or references nonexistent loop skill → must fix immediately
- **WARNING**: Stale reference, false summary, doctrine drift, or missing operational validation → fix in next cleanup
- **INFO**: Optimization opportunity, no functional impact
