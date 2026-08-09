---
name: rkx-loop-core
description: "Internal protocol for explicit RKX wave investigations: Merger bootstrap planning, parallel evidence slots, Chat summary ALWAYS (5 parts), 17 molecules, Root-depth gating, state merging, and next-wave specs."
user-invocable: false
disable-model-invocation: true
---
# rkx-loop-core

Use this internal skill only after an explicit `/rkx-loop` or `/loop-bug`.
Ordinary code work stays direct: focused inspection, the minimal safe change,
and proportionate validation. Wave protocol owns evidence collection; **Chat summary
ALWAYS** owns the final user-facing report. `loops/<run>/` is evidence SoT and
never replaces the chat report.

## Safety boundaries

- L1 is evidence and planning only. Product edits require an explicit
  `Smash` request. `Build` assembles and validates; it is not Docker permission.
- Docker requires a green `Build` validation and explicit `Ship` or
  `Build docker`. Never write secrets to artifacts or use destructive Git.
- Before editing `nginx/`, create the required timestamped sibling copy.
- The orchestrator invokes one token-mode fact slot for preflight, then writes
  only the exact matching `wave-N/preflight.yaml`; it never writes manifests,
  specs, slot reports, decisions, state, root graphs, ledgers, or product
  files. All other loop-artifact persistence remains with `merger`; after the
  L2 gate, it delegates implementation to `implementer` with the approved
  implementation scope/plan and relevant Merger scenario, state, and root-cause
  evidence.
- `implementer` may only execute that approved scope. It does not broaden the
  diagnosis, dispatch checker slots, or override Merger/Boss; it reports
  changed files and relevant validation to the caller.

## Delegation packet

Every delegation, follow-up, and Merger/Boss handoff carries this compact
envelope:
`TASK`, `SCOPE`, `ARTIFACT_REFS`, `DELTA`, `OPEN_EVIDENCE_GAP`,
`ALLOWED_TOOLS`, `OUTPUT_SCHEMA`, and `STOP_CONDITION`. Reference prior loop
artifacts; do not paste raw slot transcripts, full logs, or unchanged code
again. A later wave or tool call is valid only when the prior packet records a
specific unresolved gap.

## Merger planning contract

The first Merger call is a **bootstrap planner**, not a post-wave merge. It
receives the scenario and available initial evidence, writes the manifest and
returns a `BOOTSTRAP_WAVE_SPEC`. The orchestrator does not invent the initial
hypotheses or slot questions; it validates the spec and dispatches it.

### `CAPABILITY_PREFLIGHT`

Before every fan-out, the orchestrator invokes and awaits exactly one
token-mode `fact-slot` with group `PREFLIGHT`. The subagent returns capability
observations for every planned slot: source/tool/MCP availability,
authenticated context, read-only scope, `correlation_refs`, and
code/catalog/config revision compatibility. The orchestrator validates the
exact `spec_revision` and writes a write-once `preflight.yaml`.

Preflight is neither a wave nor a fan-out slot: it never joins the fan-in,
starts Advocate, or invokes Merger. A `STALE_SCOPE` result returns the spec to
Merger. For `WAITING_USER` or `BLOCKED`, ask USER exactly one choice:
**check as-is**, **provide what is needed**, or **stop**. Never
represent `not checked` or an unsearchable key as `not found`.

`preflight.yaml` is a `CAPABILITY_PREFLIGHT` artifact with
`schema_version: 1`, `preflight_spec_revision`, and
`orchestrator_resolution: DISPATCH_READY|STALE_SCOPE|WAITING_USER|BLOCKED|STOPPED`.
Each planned slot records `slot_id`, `status: READY|WAITING_USER|BLOCKED`,
availability, authentication state, read-only scope, correlation refs, and
revision compatibility. Only `READY` slots dispatch. A non-ready `REQUIRED`
slot follows the single user-choice flow; a non-ready `OPTIONAL` slot is saved
as skipped/degraded and does not block the READY fan-out. A slot with
`searchability: UNKNOWN` is never dispatched without the recorded user choice.

After every completed wave, the next Merger call first persists each bounded
slot report separately, then synthesizes the wave and plans the next decision.
It returns exactly one of:

- `NEXT_WAVE_SPEC` — evidence-backed hypotheses, slots, and expected facts;
- `END` — root-depth gate passed with root confidence at least `96%`;
- `HARD_BLOCKER` — the missing source/access is named with exactly one next
  check. This is provisional until the **HARD Advocate** pass and its one
  bounded recovery handoff complete.

Merger may refine, reject, split, or replace hypotheses only from supplied
evidence. A fact-slot never creates a diagnosis. The orchestrator executes the
returned spec and owns dispatch timing, but does not replace Merger's
hypothesis or root-depth decision.

### DUAL ADVOCATE GATE (soft ≥96% / hard <96%)

`Advocate (devil)` is the existing read-only runtime alias, bound to the verified Advocate model /
`__MODEL_ADVOCATE__`; it is not a new tool or role. After every **post-wave** Merger
decision, first check `root confidence` and Root-depth, then choose mode:

1. **SOFT** — `root >= 96%` and Root-depth PASS. Success is locked; no next
   wave starts. Run exactly one advisory Advocate audit. Soft cannot undo the
   locked success, cannot spawn a wave, and cannot start recovery.
   - `CLEAN` → deliver Chat summary; no HOLE block.
   - `HOLE` → deliver Chat summary plus optional `### HOLE` advisory block
     (max 2 paragraphs). `SINGLE_NEXT_CHECK` is shown to USER; follow-up dig
     starts only on explicit USER command.
2. **HARD** — `root < 96%` (or incomplete Root-depth / `HARD_BLOCKER` path).
   Run exactly one hard Advocate pass before dispatch/accept/stop, same as the
   former ALWAYS-ON gate:
   - `NEXT_WAVE_SPEC` + `CLEAN` → dispatch recorded gaps.
   - `HOLE` → one falsifiable `SINGLE_NEXT_CHECK` as one-check NEXT or one
     interpretive re-synthesis.
   - `HARD_BLOCKER` → one `BLOCKER_RECOVERY` Merger handoff.

Bootstrap and individual slots never receive an Advocate pass. Soft does **not**
replace hard: soft is only on the locked-success path; hard remains for `<96%`.

Each post-wave decision has a unique `decision_id`. Record `advocate_mode`
(`soft`|`hard`), `advocate_status`, `advocate_passed`, and
`recovery_attempted` against that identity so retries cannot duplicate the
gate. `needs_devil` may remain in legacy payloads but is informational only.
`devil` returns only `ATTACK_PACKET` and neither writes artifacts, spawns
slots, nor decides the Merger outcome.

### Confidence format law

Every confidence value emitted by any source, fact-slot, Merger, hypothesis,
root graph, or decision is a percentage in the inclusive range `0%`–`100%`.
The field is mandatory. Never emit `high`, `medium`, `low`, decimal fractions
such as `0.92`, `approximately`, or `NOT_STATED`. If the underlying source
uses a qualitative label, the responsible agent converts it to a percentage
and records the evidence basis; it must not copy the qualitative label.

### `WAVE_SPEC` payload

The machine-readable payload is YAML or JSON and is stored in the wave
artifact as `spec.yaml` (the returned chat handoff contains only the compact
payload and artifact references). The top-level `blueprint` envelope remains a
compatibility name; its semantic content is the selected reference catalog and
its entries:

```yaml
schema_version: 1
kind: BOOTSTRAP_WAVE_SPEC # BOOTSTRAP_WAVE_SPEC | NEXT_WAVE_SPEC | WAVE_DECISION
run_id: <run-id>
wave_id: 1
token_mode: API # API | CURSOR
billing_credential_scope: API_CREDENTIALS # API_CREDENTIALS | CURSOR_SUBSCRIPTION
spec_revision: <immutable run/wave/slot fingerprint>
decision_id: <post-wave-unique-id or null for bootstrap>
decision: NEXT_WAVE_SPEC | END | HARD_BLOCKER | null
advocate_mode: soft | hard | null
advocate_status: NOT_REQUIRED | PENDING | CLEAN | HOLE
advocate_passed: false
recovery_attempted: false
recovery_class: NONE # NONE | CAPABILITY_RECOVERY | EVIDENCE_CHANGING_RECOVERY
requires_user_action: false
confidence: "<0%–100%>"
confidence_basis: <evidence-based reason>

root_depth:
  q1_final_logical_status: <yes|no|not_evaluated>
  q2_deep_cause_explained: <yes|no|not_evaluated>
  q3_need_deeper_dig: <yes|no|not_evaluated>
  q4_next_layer_question: <question or null>

synthesis:
  changed_leading_explanation: <fact reference or null>
  contradicting_or_weakening_evidence: [<artifact reference>]
  unproven_root: <candidate or null>
  single_next_check: <check or null>

blueprint:
  registry_path: ${CONTROL_PLANE_ROOT}/reference/blueprint-index.yaml
  selection:
    problem_domains: [<registry domain tags>]
    route_basis: domain_routes | explicit_user_scope | mixed_scope_split
  selected_catalogs:
    - catalog_id: system-design | telephony
      index_path: <selected catalog index>
      catalog_root: <selected local root>
      catalog_revision: <pinned commit or catalog revision>
  catalog_root: <legacy single-catalog alias or null>
  index_path: ${CONTROL_PLANE_ROOT}/reference/blueprint-index.yaml
  catalog_revision: <legacy selected revision or null>
  discovery_enabled: <true|false>
  candidates:
    - blueprint_id: <stable id or compatibility alias>
      reference_id: <canonical stable reference id>
      catalog_id: <system-design|telephony>
      reference_type: <reference_architecture|call_flow|deployment_architecture|protocol_profile|interconnection_specification|legacy pattern type>
      authority: <IETF|SIP Forum|3GPP|catalog source>
      scope: <normative|industry_profile|reference_architecture|informative>
      source_refs: [<index/source anchors>]
      applicability: "<0%–100%>"
      relation: <root_zone|causal_predecessor|unrelated|unknown>
      verification_targets: [<invariant|contract|failure_mode|flow_transition|protocol_requirement|deployment_boundary|reference_architecture|interconnection_contract>]
      expected_evidence: <one concrete trace/config/code/runtime observation>
      confidence: "<0%–100%>"
      confidence_basis: <evidence-based reason>
  eligible_zones:
    - zone_id: <stable zone id>
      code_refs: [<file:symbol:lines>]
      relevance: "<0%–100%>"
      evidence_refs: [<artifact reference>]
      confidence: "<0%–100%>"
      confidence_basis: <evidence-based reason>
  qualified_pairs:
    - pair_id: <zone-id>:<blueprint-id>
      zone_id: <eligible zone id>
      blueprint_id: <qualified candidate id>
      reference_id: <canonical qualified reference id>
      catalog_id: <selected catalog id>
      reference_type: <reference entry type>
      zone_relevance: "<0%–100%>"
      reference_applicability: "<0%–100%>"
      blueprint_applicability: "<legacy alias; equal when present>"
      relation: <root_zone|causal_predecessor>
      verification_targets: [<invariant|contract|failure_mode|flow_transition|protocol_requirement|deployment_boundary|reference_architecture|interconnection_contract>]
      impact_targets: [<root_hypothesis|remediation_plan|root_confidence>]
      evidence_refs: [<artifact reference>]
  coverage_decision: <NOT_EVALUATED|REQUIRED|OPTIONAL|NOT_NEEDED>
  coverage_required: <derived boolean; true only for REQUIRED>
  coverage_reason: [<machine-checkable reason codes>]
  coverage_budget:
    max_pairs: <declared bound or null>
    overflow_action: <TRIAGE|DEGRADED_BATCH|BLOCKED>

hypotheses:
  - id: H-1
    statement: <evidence-backed candidate>
    state: <CANDIDATE|SUPPORTED|WEAKENED|REJECTED>
    confidence: "<0%–100%>"
    confidence_basis: <evidence-based reason>
    evidence_refs: [<artifact reference>]

slots:
  - slot_id: LOGS-1
    group: LOGS
    task: <one bounded task>
    hypothesis_id: H-1
    scope: <one source or hypothesis>
    expected_fact: <one checkable fact>
    expected_decision_change: <how this fact can change root/plan/confidence>
    requirement: REQUIRED # REQUIRED | OPTIONAL
    correlation_refs: <safe source/key aliases or null>
    searchability: KNOWN # KNOWN | UNKNOWN | NOT_APPLICABLE
    allowed_tools: [<tools>]
    output_schema: FACT_EVIDENCE_PACKET # FACT_EVIDENCE_PACKET | SCOUT_CANDIDATES_PACKET

dispatch:
  mode: parallel
  join: merger

artifacts:
  prior_wave: <path or null>
  output_dir: loops/<run>/wave-1/slots/

stop_condition:
  success: root confidence >= 96% and q1 == yes and q2 == yes and q3_need_deeper_dig == no
  blocker: missing source/access plus exactly one next check
```

`token_mode` determines the executor and billing/credential path, not the
model policy: `API` uses the API credentials path and `CURSOR` uses the Cursor
subscription path. The value never contains a credential, account identifier,
or secret. `spec_revision` is an immutable fingerprint of the run, wave, and
planned slots; preflight must echo it exactly.

For `BOOTSTRAP_WAVE_SPEC`, `decision` is null, Root-depth is `not_evaluated`, and the initial
evidence-backed hypotheses are the planning input. Reference `candidates` and
`qualified_pairs` are empty at bootstrap; `coverage_decision` is
`NOT_EVALUATED`. A `NEXT_WAVE_SPEC` uses `kind: NEXT_WAVE_SPEC` and
`decision: NEXT_WAVE_SPEC`. Terminal decisions use `kind: WAVE_DECISION`
and `decision: END|HARD_BLOCKER`; their `slots` are empty and the
Root-depth answers and evidence references are mandatory. `decision_id`,
`decision`, and advocate fields are required only for post-wave decisions.
Post-wave Advocate uses dual-mode:
`advocate_mode: soft` when `root >= 96%` (advisory), `hard` when `root < 96%`.
A `BLOCKER_RECOVERY` handoff reuses the original blocker `decision_id`; it is a
bounded completion of the hard gate, not a second post-wave decision or a
second Advocate pass. `CAPABILITY_RECOVERY` keeps that decision id. An
`EVIDENCE_CHANGING_RECOVERY` creates a new decision id and must pass a new
Advocate gate.

### Reference qualification gate

System Design Primer, IETF RFCs, SIPconnect and 3GPP entries are catalogs of
references, not one universal architecture and not a project coding standard.
Scout
candidates become coverage pairs only after Merger qualification.
`qualified_pairs` is the dispatch set; the full candidate-zone/catalog
Cartesian product is never the default.

For each qualified pair, all of the following must be present:

```text
zone_relevance >= 70%
reference_applicability >= 70%
blueprint_applicability >= 70% when the legacy field is present
relation = root_zone | causal_predecessor
verification_target ∈ invariant | contract | failure_mode | flow_transition | protocol_requirement | deployment_boundary | reference_architecture | interconnection_contract
impact_targets ∩ {root_hypothesis, remediation_plan, root_confidence} ≠ ∅
evidence refs + CONFIDENCE_BASIS for every percentage
```

`coverage_decision` is derived as follows:

- `REQUIRED` — at least one qualified pair passes the predicate and checking it
  can change the root hypothesis, remediation plan, or root confidence;
- `OPTIONAL` — a candidate is relevant but cannot change the current
  investigation outcome; keep it as a reference without launching coverage;
- `NOT_NEEDED` — no candidate/zone pair satisfies the predicate;
- `NOT_EVALUATED` — Bootstrap has not yet merged Scout evidence.

`coverage_required: true` is valid only for `REQUIRED`. If the declared
`coverage_budget` is exceeded, Merger must triage with one bounded check or
declare bounded degraded batches; it must not silently drop qualified pairs.

### Durable wave layout

```text
loops/<run>/
  manifest.md
  state.md                  # rolling compressed state
  wave-1/
    spec.yaml
    slots/
      LOGS-1/report.md
      CODE-1/report.md
    merge.md
    state.md
    root-graph.md
    ledger.md
  wave-2/
    ...
```

`report.md` is the bounded slot report. Use `raw.md` only when a verbatim
provider/tool response must be preserved; raw chat transcripts do not belong
in rolling state.

## Parallel dispatch contract

- Independent slots in one wave are a **fan-out set**. Once the manifest and
  slot packets are ready, dispatch all LOGS, CODE, DOCS, applicable DATA and
  `BLUEPRINT-SCOUT` slots in one parallel delegation batch. A later
  `REFERENCE-COVERAGE` fan-out dispatches only Merger-qualified pairs.
  `BLUEPRINT-COVERAGE` is accepted as a legacy group label only.
- Groups are scope labels, not serial stages. Never wait for one slot or group
  to finish before launching another independent slot, and never dispatch
  slots through a one-by-one loop.
- Checker slots are read-only and must not write shared run artifacts. Results
  may arrive in any order; the post-wave Merger persists each returned packet
  under `wave-N/slots/<slot-id>/report.md` before synthesis.
- `merger` is the **join barrier**: delegate it once after every slot returns
  or has an explicit terminal failure. Do not start a merger per slot.
- Later waves remain dependency-ordered after the merger, but every independent
  slot inside each later wave uses the same parallel fan-out.
- If a runtime concurrency cap prevents a full fan-out, use the largest
  bounded concurrent batch and mark the run degraded; intentional
  one-at-a-time dispatch is not allowed.

## Wave protocol

1. Ask the user to choose token mode: **API** or **Cursor**. If unspecified,
   ask rather than assume. API waves dispatch `fact-slot`; Cursor-token waves
   dispatch `cursor-fact-slot` only after the caller resolves the concrete
   runtime ID in the picker/catalog. Never silently substitute a model.
2. Delegate the first Merger in bootstrap mode with the scenario, initial
   evidence references, and token mode. Wait for `BOOTSTRAP_WAVE_SPEC` before
   dispatching Wave 1.
3. Before dispatching the first or any later wave, invoke and await one
   token-mode `fact-slot` with group `PREFLIGHT`, validate its
   `CAPABILITY_PREFLIGHT` packet against the exact spec revision, and persist
   `preflight.yaml`. Only READY slots enter fan-out.
4. The default first spec covers **LOGS + CODE + DOCS**. Add **DATA** only
   when the scope actually includes a database or external API contract. When
   the local reference registry is available, Bootstrap selects relevant
   catalogs and adds bounded `BLUEPRINT-SCOUT` slots with explicit
   `CATALOG_ID` values to the same fan-out.
5. A spec has 1–10 narrow slots per group. Each slot has exactly one
   hypothesis/source and one expected fact. A Scout slot returns zero to three
   candidate reference patterns; a `REFERENCE-COVERAGE` slot checks exactly one
   `qualified_pair`. Dispatch all independent slots concurrently. Slots are
   fact collectors: evidence, source anchor, confidence, and missing
   information—no verdicts.
6. After the fan-out join, delegate one post-wave Merger. It persists every
   slot report under the wave's `slots/` directory, writes `merge.md`,
   `state.md`, `root-graph.md`, and `ledger.md`, then records the synthesis
   check and answers the Root-depth gate. The synthesis check is not a
   replacement for Root-depth:
   - What fact changed the leading explanation?
   - What evidence contradicts or weakens it?
   - Which root remains unproven?
   - What single next check most reduces uncertainty?
When Scout packets are present, Merger also qualifies eligible zones and
candidate reference entries, builds sparse `qualified_pairs`, and records
   `coverage_decision` as `REQUIRED`, `OPTIONAL`, or `NOT_NEEDED`. `REQUIRED`
   is allowed only when every qualification predicate is evidenced.
7. The canonical Root-depth questions are:
   - Is this the final logical status of the answer?
   - Does this explain the root cause (not a label/symptom)?
   - Is a deeper investigation still needed?
   - What next question will open another layer (down to API/runtime/language
     semantics if needed)?
8. After every post-wave Merger decision, select Advocate mode in this order:
   - `decision: HARD_BLOCKER` → go to step 10 (**HARD**) regardless of
     root confidence.
   - `root >= 96%` and Root-depth PASS → success locked; go to step 9 (**SOFT**).
   - `root < 96%` / incomplete Root-depth → go to step 10 (**HARD**).
   Do not repeat completed slots.
9. **SOFT path.** Delegate `Advocate (devil)` exactly once for this
   `decision_id` (the verified Advocate model / `__MODEL_ADVOCATE__`, picker-verified) as an
   advisory audit. Soft cannot undo the locked 96% success and cannot
   auto-trigger a next wave.
   - `CLEAN` → deliver the final five-part Chat summary. No HOLE block.
   - `HOLE` → deliver Chat summary plus optional `### HOLE — identified gap`
     (max 2 paragraphs). Show `SINGLE_NEXT_CHECK` to USER; follow-up dig only
     on explicit USER command.
10. **HARD path.** Delegate `Advocate (devil)` exactly once before
   dispatch/accept/stop with the compact packet (decision identity, leading
   root, Root-depth, synthesis, reference predicates, blocker/access state,
   artifact refs). `devil` returns `ATTACK_PACKET` only; it does not write
   `loops/**`, spawn slots, decide the outcome, or replace `boss`.
   - `NEXT_WAVE_SPEC` + `CLEAN` → dispatch documented gaps via parallel fan-out.
   - `HOLE` → one falsifiable `SINGLE_NEXT_CHECK` as one-check NEXT or one
     interpretive Merger re-synthesis.
   - `HARD_BLOCKER` → exactly one `BLOCKER_RECOVERY` handoff under the original
     `decision_id`. Merger returns either a one-check `NEXT_WAVE_SPEC` or the
     same blocker with `recovery_attempted: true` and the precise precondition.
     Only the confirmed recovery blocker may stop. Do not invent unavailable
     access or spin after one recovery attempt.
11. Never run a Merger⇄Advocate chat loop and never run a second Advocate on
    the same `decision_id`. Soft does not replace hard. Terminal `END` (after
    soft CLEAN/HOLE) or a confirmed recovery blocker must deliver the full
    five-part English Chat summary; mid-wave stays at one status line or silence.

## Evidence routing

Start with direct targeted Read/search. Use logs, docs, and data only when the
question makes them relevant. Use Tenets only when scope remains unknown after
targeted inspection. Use CodeGraph or Octocode only for a structural, caller,
trace, reference, or impact gap; add the other only if that gap persists.
Use Crash for large evidence synthesis or competing hypotheses. Postgres access
remains read-only. Durable memory is the run artifact set, not raw chat history.

## Report canon (5 columns)

| Current state | What is broken and why | What to fix and how | Technical-documentation validation | State after the fix |
|---|---|---|---|---|

- “Current state / after” — UI/business + code anchors (module / file:line / symbol).
- For result status, see **Part 5) Verdict** below (not harness status).
- A 3-column chat report is a compression, not a replacement for the canon in the Chat summary / `findings.md`.

## Chat summary ALWAYS (UNIVERSAL — any `/loop-*` / `/rkx-loop`)

**MUST** write the full result in the USER chat in **English** on the **first** delivery of
leaf / L1 STOP / phase conclusion / validate verdict / accepted `END` / confirmed
recovery `HARD_BLOCKER`.
`loops/<run>/**` is the evidence SoT; **do not** replace the chat report with a run path.

### Definition of “full Chat summary delivered” (binding)

Count the leaf/result as **delivered** (`milestone chat_itog_delivered`) **only
when the USER chat already contains all 5 parts below in one response**.
A result **without the ASCII diagram**, **without the 5-column table**, or
**without the human Part 5** is **NOT delivered** (contract FAIL) — do not
continue with silent / “unchanged leaf” / “recorded in the wave”.

Self-check before sending (all ✅ or STOP):

| # | Part | Required? |
|---|---|---|
| 1 | Business/UI in one sentence | ✅ |
| 2 | **5-column** table (Markdown table) | ✅ |
| 3 | Concrete technical facts (path/symbol/conf%) | ✅ |
| 4 | **ASCII / box-drawing flow diagram** (molecule 12) | ✅ |
| 5 | **Human verdict** — template below | ✅ |

Harness/wave metrics (`WAVE_SPEC`, Root-depth, conf%, phase) live in Part **3**
and/or `loops/<run>/` — **not** instead of Part 5.

### Part 5) Verdict — binding template (for USER, not the harness)

**Required structure:**

```markdown
### 5) Verdict

**✅|❌ <business statement> — N%**
<One sentence explaining what the result means for the UI/business; no harness jargon.>
*synthesis: <actual role that assembled the conclusion> · <Model Name actually used> · <wave artifact / validation evidence>*

**How the verification works**

1. <First causal link in the UI, business, data, integration, operations, or regression scenario.>
   **Basis:** *<fact translated into UI/service behavior; add a short technical anchor only when needed>*
   **Where:** *<evidence-id: SLOT-ID / validator / browser / diff> · N% · <Model Name actually used>*

2. <Next causal link; the number of items is arbitrary and determined by the verified chain.>
   **Basis:** *<fact expressed in scenario language>*
   **Where:** *<evidence-id> · N% · <Model Name actually used>*

<Continue for as many links as are actually proven. Do not add empty items or replace the chain with an unrelated list of clusters.>

**Tail / blocker:** <only if it actually exists; explain what it means for the user.>
**Where:** *<evidence-id> · N% · <Model Name actually used>*
**Advocate:** *<actual model · soft|hard · CLEAN|HOLE|not run; do not present role binding as execution fact>*
```

The number of causal items is not limited or prescribed by the example. Each item must have exactly two `Basis` and `Where` lines. If one item relies on multiple independent facts, list the complete `evidence-id · N% · model` triples in one `Where` line, separated by `;`.

### Soft advisory block `### HOLE — identified gap` (after Part 5)

Only for the **SOFT** path (`root >= 96%`) when `ATTACK_STATUS: HOLE`. This is **not**
a required sixth part: `chat_itog_delivered` still requires exactly 5
parts. Do not output this block for soft-`CLEAN`. Hard-`HOLE` follows the hard
continuation mechanism, not this terminal soft block.

Contract (strictly **no more than 2 paragraphs**):

```markdown
### HOLE — identified gap (advisory)

<Paragraph 1: what is unproven and why it does not invalidate the current ≥96% result.>

**SINGLE_NEXT_CHECK:** <one falsifiable check> + impact on UI/business. *<evidence-id · N% · model; Advocate · model (role binding)>*
```

Rules:
- More than two paragraphs is forbidden; put details in `loops/<run>/`.
- Soft-`HOLE` does not invalidate `≥96%` and does not auto-start a next wave; follow-up
  requires an explicit USER command.
- In Part 5, `Advocate:` states `soft · HOLE` without duplicating this block.

`Basis:` and `Where:` are **bold only as labels**; their content is *italicized*. Each fact gets one exact confidence value `N%`; ranges, `high`/`medium`/`low`, decimal values, and `NOT_STATED` are forbidden.

**Full canonical example:**

```markdown
### 5) Verdict

**❌ Operators are not visible — 94%**
The UI shows an empty saved candidate list after provider synchronization
failed; the commit is not the cause.
*synthesis: Merger · the verified Merger model (role binding) · wave-1 merge / root-graph*
*Execution models are not recorded in the source evidence artifacts; the role binding below is not an execution fact.*

**How the verification works**

1. The configuration screen does not search for operators itself — it only
   renders the list from saved workspace settings.
   **Basis:** *the frontend takes options only from users / availableUsers; there is no separate source.*
   **Where:** *CODE-1 · 92% · the verified checker model (role binding)*

2. The operator list saved in this workspace's settings is empty → the dropdown
   contains only `Unassigned`.
   **Basis:** *the workspace configuration contains an empty operator list
   (`available_users=[]`).*
   **Where:** *DATA-1 · 96% · the verified checker model (role binding)*

3. This is not “the wrong account”: the selected resource and the empty
   operator list belong to the same workspace.
   **Basis:** *the provider resource and workspace configuration resolve to one
   workspace/tenant.*
   **Where:** *DATA-1 · 96% · the verified checker model (role binding)*

4. There are enough people to assign — an empty dropdown does not mean that
   nobody is in the system.
   **Basis:** *the service has eligible operators with the required
   permissions, and the provider reports active members.*
   **Where:** *DATA-2 · 96% · the verified checker model (role binding); DATA-3 · 95% · the verified checker model (role binding)*

5. The list should be populated by syncing provider members into the service
   settings; synchronization failed, so the saved list remained empty.
   **Basis:** *schema and provider connection errors were recorded while
   updating members.*
   **Where:** *LOGS-1 · 93% · the verified checker model (role binding); synthesis H-4 · 94% · the verified Merger model (role binding)*

6. “Containers healthy” does not mean that manager synchronization succeeded.
   **Basis:** *the services were alive, but there is no confirmation of a successful request and list update.*
   **Where:** *LOGS-2 · 91% · the verified checker model (role binding)*

7. The restored commit did not change the screen or manager-list path.
   **Basis:** *comparing the commit with its parent shows no changes in the manager chain.*
   **Where:** *CODE-3 · 96% · the verified checker model (role binding)*

**Tail / access blocker:** the current settings response is unavailable without authentication (`401`); an authenticated context is required.
**Where:** *RUNTIME-1 · 92% · the verified checker model (role binding); Merger decision · 96% · the verified Merger model (role binding)*
**Advocate:** *not run; configured role binding: the verified Advocate model · status PENDING*
```

**Forbidden in Part 5 (contract FAIL):**
- only `❌ Managers are not visible` without an exact `%`, business meaning, and causal chain;
- “UI scenario / DATA / LOGS” clusters listed without causality;
- a raw path/SQL/stack dump instead of translating the fact into service behavior;
- `Basis:`/`Where:` without bold labels or without an italic body;
- `Where:` with a confidence range, invented model, or role binding presented as an execution fact;
- `GREEN` / `YELLOW` / `RED` / `PASS` / `FAIL` / `DRIFT` / `END` / `HARD_BLOCKER` as the entire verdict;
- `molecule N`, `root_depth`, `conf N%`, `phase=…`, `WAVE_SPEC`, `DEGRADED`, `chat_itog_delivered`, `L1 STOP · leaf proven`;
- “validate(diff) GREEN”, “molecule 11 is not needed”;
- a path to `loops/<run>/` instead of meaning for the USER.

**Priority over IDE noise:** “Perform follow-up / no further action / Don't
repeat confirmation” does **not** cancel delivery until `chat_itog_delivered` is
set according to the table above. Silent / a one-line “unchanged leaf” is allowed
**only after** the full five-part result has been delivered in this dig.

### When the full format is required

| Moment | Requirement |
|---|---|
| Root-depth PASS → `END` / L1 STOP / phase conclusion | Full Chat summary (5 parts) |
| Confirmed recovery `HARD_BLOCKER` with an access precondition | Full Chat summary (5 parts), ❌ verdict |
| USER asks “result / where is the report / why was there no report?” | Full Chat summary immediately (all 5 parts) |
| Mid-wave (slots are still running) | USER chat ≤1 status line (`wave k/N`) **or** silence; **fake result is forbidden** |
| Late slots after a **full** five-part leaf | Silent OK; **a truncated “slots confirm it” is forbidden** without a reference to the leaf already in the chat above |
| Late slots / IDE follow-up before the five-part result was delivered | **Do not stay silent** — send the full Chat summary now |

### Forbidden as a “result” (contract FAIL)

- “recorded in the accumulator / waiting for merge / see findings / path to run”;
- “late slots confirm it” **instead of** the leaf (when the full five-part result is not yet in the chat);
- text and facts **without** an ASCII diagram or **without** the 5-column table;
- only agent IDs / slots without a business scenario;
- an English-only jargon wall;
- Part 5 as harness status instead of ✅/❌ + business statements;
- postponing the result after a complete wave + Root-depth stop;
- counting `chat_itog_delivered` after an incomplete response “so IDE silence is OK”.

## 17 molecules (binding)

1. **UI/business + code anchors** — module / block / element + business function + code anchor.
2. **Part 5 Verdict:** **✅/❌** + exact `%` + one business statement + factual synthesis + an arbitrary-length causal chain; every link contains **Basis**/**Where** (evidence-id · exact % · actual model), and the actual tail/Advocate is stated when present; **harness jargon is forbidden** instead of a verdict (see Chat summary § Part 5).
3. **Wave Loop Cycle:** bootstrap Merger → parallel groups (**LOGS+CODE+DOCS**, DATA only for DB/API) per `WAVE_SPEC`; post-wave Merger → Root-depth → route `HARD_BLOCKER` to hard Advocate first, then use soft only for locked success; deep bug = many narrow slots; Context7/fetch ≥30 for external APIs/libs; micron; e2e; logs+Postgres. Unconditional `N≥3` floor is **not** restored — slot count comes from evidence-backed `WAVE_SPEC`.
4. **Deep RC; chat; evidence discipline** — hypotheses are explicitly marked candidates; only evidence from code/PG/logs may be presented as facts. No product edits at L1.
5. **MCP stack:** Tenets → Crash (cross-cut) → CodeGraph → Postgres; Octocode on narrow anchors. Evidence-driven, not a fixed sequence.
6. **Success criteria + antipatterns** (ponytail ladder in the plan).
7. **Logs-first (inside wave LOGS group):** `${CONTROL_PLANE_ROOT}/runtime/logs/README.md`
   and explicitly approved external log locations → service access/error logs
   → container logs — top-k, **do not** skip. LOGS-group slots start in the
   first parallel wave together with DOCS/CODE.
8. **Token economy + slots + retrieval:** the actually selected models are recorded at dispatch and in evidence artifacts; `CURSOR-MODELS.md` is only policy/binding, not execution evidence; top-k ~20; no full ZZ/log dump.
9. **Crash checks + dual Advocate:** final truth? Soft ≥96% (advisory HOLE block, no auto-next); hard <96% (gate continues). Soft does not replace hard.
10. **No hacks / hardcodes / BP breaks / plan violations** + ponytail YAGNI/reuse.
11. **Revert-first by diff:** if validate(diff) is red — attribution FACT ONLY; our L2 → revert hunks → re-plan; not ours → evidence/STOP; surgical forward only with the USER’s `surgical`/`Smash` request.
12. **ASCII / box-drawing** flow diagram in findings/plan/chat (required in Chat summary Part 4).
13. **Biz+dev path walk** end-to-end (user scenario + API/UI/logs/PG).
14. **Reviewer stance:** honest and independent; do not criticize for criticism's sake.
15. **Startup lens** optional (`--lens startup`).
16. **Validate edits explicitly** — after L2, validate(diff) is mandatory in full.
17. **Consistency:** after editing plan/skills/rules — todos↔body↔mermaid↔atoms↔ADR/sources/tiers; FAIL → edit the document.

Wave artifacts and Root-depth answers remain mandatory internal evidence. They
do **not** replace the Chat summary. Do not replace the canonical Root-depth questions
with an arbitrary questionnaire.

## Easy summary artifact

At a terminal Cursor `stop` event, the project hook
`${CONTROL_PLANE_ROOT}/hooks/rkx_write_easy_summary.py` looks up the terminal
`slack-notification.json` for the current conversation and writes a compact
`easy-summarize.md`. A terminal lifecycle artifact may name one validated,
workspace-relative `capture_dir`; otherwise the file is written under
`loops/<run>/`. The hook is fail-open, conversation-scoped, and copies only
safe lifecycle/decision fields. It never copies raw slot transcripts, logs,
credentials, or the full Chat summary, and it never reconstructs a verdict
when confidence or model evidence is absent. The five-part Chat summary in
Cursor remains the canonical user-facing report; `easy-summarize.md` is a
compact local export.

## Slack notify (phone)

Built-in Cursor Slack integration notifies only for **Cloud Agents** started
from Slack/web (see https://cursor.com/docs/integrations/slack). Local IDE
Agent Chat does **not** get that DM automatically.

Local RKX uses two separate message classes:

1. **Attention card:** the deterministic `stop` hook
   (`${CONTROL_PLANE_ROOT}/hooks.json` → `${CONTROL_PLANE_ROOT}/hooks/rkx-slack-notify.sh`) reads only the
   run-scoped `loops/<run>/slack-notification.json`, matches the current
   `conversation_id`, and posts via Incoming Webhook or `chat.postMessage`
   only when the user must answer or decide (`waiting_user`, `blocked`,
   `failed`, `wave_cap`).
2. **Result card:** the same hook posts exactly once for a completed loop
   (`completed`) and labels it `Work summary`.
3. **Full verdict:** after the complete Chat summary is delivered in Cursor, the
   orchestrator may send one separate full verdict via
   `plugin-slack-slack` / `slack_send_message`. The full verdict keeps the
   canonical five-part format and is never reconstructed from `state.md`.
   Hook and MCP ownership must not send the same class twice.

`started` and `progress` remain valid lifecycle artifacts for auditability but
are not sent to Slack. New artifacts must carry the exact active
`conversation_id` and a `notification_type` of `attention` or `result`;
placeholder IDs are invalid. Older artifacts without `notification_type` are
classified from `kind` for compatibility. The hook selects the newest sendable
artifact, claims its event under an exclusive short lease, and retains a
successful delivery record for at least the artifact-age window. A process
failure after external delivery may still permit one bounded retry because an
Incoming Webhook offers no idempotency key. Missing/mismatched artifacts and
Slack failures remain fail-open. When the transport is a channel Incoming
Webhook, `SLACK_NOTIFY_MENTION` addresses the configured recipient so Slack can
generate a mobile push; the value belongs only in
`${HOME}/.cursor/rkx-slack-notify.env`.

**Lifecycle artifact contract:**

```json
{
  "schema_version": 1,
  "conversation_id": "cursor-conversation-id",
  "event_id": "unique-lifecycle-event",
  "run_id": "2026-08-07-rkx-example",
  "wave": "wave-1",
  "kind": "waiting_user",
  "notification_type": "attention",
  "problem_title": "Operators are not visible in the configuration list",
  "summary": "The service shows an empty list because the saved workspace settings did not receive operators from the provider.",
  "blocker": "Verification hit a 401 without authentication.",
  "next_action": "Open an authenticated Browser Tab and repeat the read-only check.",
  "capture_dir": "rkx_capture_2026-08-08",
  "decision_artifact": {
    "path": "loops/2026-08-07-rkx-example/wave-1/merge.md",
    "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "full_verdict_available": false
}
```

`problem_title` preserves the original user scenario, not an unconfirmed
hypothesis. `summary`, `blocker`, and `next_action` must be understandable
without RKX context. Do not write tokens, secrets, raw slot transcripts,
unnecessary PII, or the full Chat summary to the artifact.

**Lifecycle card (EN):**

```text
<status> <detailed problem title>

<what this means for the user>
Blocker: <only if present>
Next step: <one concrete action>

<run> · <wave>
```

Percentages, evidence, and actual models are shown only in the full verdict
when they are genuinely recorded in the evidence artifacts. A working link to
the full result may be added as a normal Markdown link; interactive
`Continue verification` / `Stop` controls require a separate callback/backend
and must not be shown as dead buttons.

Phone delivery = Slack mobile app push for that DM/channel. Credentials live
only in `${HOME}/.cursor/rkx-slack-notify.env` (never in git).
