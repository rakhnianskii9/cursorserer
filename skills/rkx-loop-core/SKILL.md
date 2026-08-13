---
name: rkx-loop-core
description: Use when an explicit rkx-loop or loop-bug requires the RKX wave protocol, Merger bootstrap or merge, parallel evidence slots, Root-depth gating, state or decision artifacts, or the Chat summary contract.
---
# rkx-loop-core

Canonical packet topology, ownership, and transitions:
`RKX-LOOP-BLUEPRINT-FLOW.md`. Orchestrator is readonly and executes only a
`ControllerAction`. Merger writes shared state including
`wave-<n>/preflights/<revision_seq>.yaml`. Advocate runs once per
`proposal_id`; `decision_id` appears only after settlement. Token modes are
`API | CURSOR` only.

Use this internal skill only after an explicit `/rkx-loop` or `/loop-bug`.
Ordinary code work stays direct: focused inspection, the minimal safe change,
and proportionate validation. Wave protocol owns evidence collection; **Chat summary
ALWAYS** owns the final user-facing report. `loops/<run>/` is evidence SoT and
never replaces the chat report.

## Safety boundaries

- L1 is evidence and planning only. Product edits require
  `implementation_authorized=true` on the original request, or a later
  explicit L2 gate (`Smash`). `Build` assembles and validates; it is not
  Docker permission.
- Docker requires a green diff validation and explicit `Ship` or
  `Build docker`. Never write secrets to artifacts or use destructive Git.
- Before editing `nginx/`, create the required timestamped sibling copy.
- The orchestrator is readonly. It invokes one token-mode fact slot for
  preflight and forwards the CapabilityPacket to `merger`; Merger writes
  `loops/<run>/wave-<n>/preflights/<revision_seq>.yaml`. The orchestrator
  never writes manifests, specs, slot reports, decisions, state, root
  graphs, ledgers, summaries, lifecycle artifacts, or product files. After
  the L2 gate, it delegates implementation to `implementer` with the
  approved ImplementationRequest.
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

### Success criteria (UNIVERSAL — any `/rkx-loop` / `/loop-*`)

`problem_title` preserves the USER's original wording. It is **not** the
product PASS condition. Every run must also record `success_criteria`.

| Field | Meaning |
|---|---|
| `problem_title` | Verbatim USER scenario / symptom phrasing |
| `success_criteria.statement` | Concrete PASS in USER/business language (what must work) |
| `success_criteria.source` | `user_explicit` \| `user_inferred_confirmed` \| `title_only_scope` |
| `goal_closure.question_answered` | Title/dig question closed with evidence |
| `goal_closure.product_goal_met` | `success_criteria` PASS/FAIL evidenced |
| `goal_closure.title_only_scope` | `true` only when USER explicitly scoped dig to the title phrase alone |

**Bootstrap rules (all loops):**

1. Write both `problem_title` and `success_criteria` into `manifest.md` and
   `BOOTSTRAP_WAVE_SPEC` before Wave-1 fan-out.
2. Prefer `user_explicit` from the USER message. If the title/keywords can be
   read as a side topic while the USER's real PASS is a product scenario
   (works / broken / matrix of surfaces), do **not** invent PASS — ask exactly
   one grill question and set lifecycle `waiting_user` until answered, **or**
   get an explicit `title_only_scope` confirmation.
3. `user_inferred_confirmed` is allowed only when the USER already stated the
   PASS in the same conversation (not guessed from a keyword in the title).
4. Evidence-first over title keywords: when capture/logs/runtime evidence shows
   a stronger product failure mode than a title keyword side-quest, leading
   hypotheses follow the evidence. Title-only side checks stay `OPTIONAL`
   unless `title_only_scope: true`.

**END / Root-depth rules (all loops):**

- Soft-path candidate `END` requires `root >= 96%`, Root-depth PASS, **and**
  `goal_closure.product_goal_met: yes` — unless `title_only_scope: true`, in
  which case `question_answered: yes` may suffice and must be disclosed in
  Chat summary.
- Forbidden: `END` with `question_answered: yes` and `product_goal_met: no`
  when `title_only_scope` is false/absent — even if root ≥96% on a side topic.
- If `success_criteria` remains unmet and a falsifiable next check exists
  (missing access → `HARD_BLOCKER` / `WAITING_USER`; evidence gap →
  `NEXT_WAVE_SPEC`), do not soft-END on a title-keyword detour.
- Root-depth q1/q2 answer against `success_criteria`, not against a rephrased
  title keyword, unless `title_only_scope: true`.

**Advocate rules (all loops):**

- Advocate runs once per Merger `proposal_id` and returns `AdvocatePacket`
  `CLEAN` or `HOLE`. It does not write files or mint `decision_id`.
- Material `HOLE` is never an AcceptedDecision: Merger revises/mints a
  Proposal and Advocate runs again. Immaterial `HOLE` may accept with a
  recorded rationale.
- A `HOLE` next-check must advance `success_criteria` (or the named access
  needed for it). It must not reframe the dig onto a title keyword when
  `title_only_scope` is false and a product PASS remains open.

### `CAPABILITY_PREFLIGHT`

Before every fan-out, the orchestrator invokes and awaits exactly one
token-mode `fact-slot` with group `PREFLIGHT`. The subagent returns capability
observations for every planned slot: source/tool/MCP availability,
authenticated context, read-only scope, `correlation_refs`, and
code/catalog/config revision compatibility. The orchestrator validates the
exact `spec_revision` and forwards the CapabilityPacket. Merger writes a
write-once `wave-<n>/preflights/<revision_seq>.yaml`. Singleton
`preflight.yaml` is not canonical.

Preflight is neither a wave nor a fan-out slot. Capability observation per
slot is `READY | UNAVAILABLE | STALE | INVALID` and is not a transition
action. Merger records PreflightDecision
`DISPATCH | REPLAN | WAITING_USER | HARD_BLOCKER_CANDIDATE` and returns a
`ControllerAction`. `REPLAN` mints a new spec revision; `WAITING_USER`
parks `pending_action=NONE` and `awaiting_input=USER`; a blocker candidate
goes to Advocate. Never represent `not checked` or an unsearchable key as
`not found`.

Each planned slot in the preflight artifact records `slot_id` and capability
status. Only `READY` REQUIRED slots dispatch. A non-ready OPTIONAL slot is
saved as skipped/degraded and does not block the READY fan-out.

After every completed wave: join → Merger Proposal (`proposal_id`,
`candidate_action`) → Advocate → accepted decision. Candidate actions are
exactly:

- `NEXT_WAVE_SPEC` — evidence-backed hypotheses, slots, and expected facts;
- `END` — root-depth gate passed with root confidence at least `96%` **and**
  `goal_closure.product_goal_met: yes` (or explicit `title_only_scope: true`
  with `question_answered: yes` disclosed);
- `HARD_BLOCKER` — the missing source/access is named with exactly one next
  check. This is provisional until Advocate settlement and at most one
  `BLOCKER_RECOVERY` per `proposal_id` (forbidden at wave 20 / after
  checkpoint 20).

Merger may refine, reject, split, or replace hypotheses only from supplied
evidence. A fact-slot never creates a diagnosis. The orchestrator executes
only the returned `ControllerAction` and does not replace Merger's
hypothesis or root-depth decision.

### Advocate gate (once per `proposal_id`)

`Advocate (devil)` is the existing read-only runtime alias, bound to
`__MODEL_ADVOCATE__`. After every post-wave (or checkpoint) Merger Proposal,
Orchestrator runs exactly one Advocate pass on that `proposal_id` and
forwards `AdvocatePacket` to Merger. Bootstrap and individual slots never
receive an Advocate pass. Boss is checkpoint-only (waves 10/20) and is not
this gate.

- `END + CLEAN` → accept END
- `END + HOLE` material → revised NEXT proposal; immaterial → accept END
  with recorded rationale
- `NEXT + CLEAN` → accept NEXT_WAVE_SPEC
- `NEXT + HOLE` → revised NEXT with one falsifiable check
- `HARD_BLOCKER` → `BLOCKER_RECOVERY` (≤1 REQUIRED slot) then PREFLIGHT;
  forbidden at wave 20 / after checkpoint 20; cap HARD_BLOCKER → DELIVER
  only

`decision_id` appears only after settlement. `devil` returns only
`AdvocatePacket` and neither writes artifacts, spawns slots, nor decides the
Merger outcome. Never a Merger⇄Advocate chat loop.

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
kind: BOOTSTRAP_WAVE_SPEC # BOOTSTRAP_WAVE_SPEC | NEXT_WAVE_SPEC | BLOCKER_RECOVERY_SPEC
run_id: <run-id>
phase_id: <phase-id>
wave_id: 1
token_mode: <API|CURSOR> # caller-selected execution mode
billing_credential_scope: <API_CREDENTIALS|CURSOR_SUBSCRIPTION>
spec_revision: <immutable run/wave/slot fingerprint>
revision_seq: 1
correlation_id: <request correlation id>
max_slot_attempts: 3
# proposal_id / decision_id are not WaveSpec fields; they live on Proposal / AcceptedDecision
confidence: "<0%–100%>"
confidence_basis: <evidence-based reason>
problem_title: <verbatim USER scenario>
success_criteria:
  statement: <PASS condition in USER/business language>
  source: user_explicit | user_inferred_confirmed | title_only_scope
  matrix: <optional structured checks; null if unused>
goal_closure:
  question_answered: <yes|no|not_evaluated>
  product_goal_met: <yes|no|not_evaluated>
  title_only_scope: <true|false>

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
  registry_path: .cursor/reference/blueprint-index.yaml
  selection:
    problem_domains: [<registry domain tags>]
    route_basis: domain_routes | explicit_user_scope | mixed_scope_split
  selected_catalogs:
    - catalog_id: system-design | telephony
      index_path: <selected catalog index>
      catalog_root: <selected local root>
      catalog_revision: <pinned commit or catalog revision>
  catalog_root: <legacy single-catalog alias or null>
  index_path: .cursor/reference/blueprint-index.yaml
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
  success: root confidence >= 96% and q1 == yes and q2 == yes and q3_need_deeper_dig == no and (product_goal_met == yes or title_only_scope == true)
  blocker: missing source/access plus exactly one next check
```

`token_mode` is caller-selected and must be paired with its billing/credential scope:

| token_mode | billing_credential_scope | preflight/checker | blueprint scout |
|---|---|---|---|
| `API` | `API_CREDENTIALS` | `fact-slot` | `blueprint-scout` |
| `CURSOR` | `CURSOR_SUBSCRIPTION` | `cursor-fact-slot` | `cursor-blueprint-scout` |

A Cursor caller records `CURSOR`; `API` is allowed only when API credentials are
explicitly available. Never silently substitute a route or model. The value never
contains a credential, account identifier, or secret. `spec_revision` is an
immutable fingerprint of the run, wave, and planned slots; preflight must echo
it exactly.

### Durable decision and coverage contract

Every completed wave updates canonical `loops/<run>/state/current.yaml` (CAS
on `state_revision`). `latest-decision.*` is not authoritative for new runs.
Merger persists every qualified and rejected reference pair in the
`waiver_ledger` with qualification failures and evidence refs; a waiver is
not silently dropped.

For `BOOTSTRAP_WAVE_SPEC`, Root-depth is `not_evaluated` and the initial
evidence-backed hypotheses are the planning input. Reference `candidates` and
`qualified_pairs` are empty at bootstrap; `coverage_decision` is
`NOT_EVALUATED`. A later wave uses `kind: NEXT_WAVE_SPEC`. Recovery uses
`kind: BLOCKER_RECOVERY_SPEC` with `blocker_recovery_of_proposal_id`.
Accepted transitions live on `AcceptedDecision` (`decision_id` after
Advocate settle), not on WaveSpec. A `BLOCKER_RECOVERY` is at most one spec
revision per HARD_BLOCKER `proposal_id`; a material new fact mints a new
`proposal_id` and must pass Advocate again.

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
  manifest.yaml
  state/current.yaml
  hypotheses/<rev>.yaml
  wave-1/
    specs/<revision_seq>.yaml
    preflights/<revision_seq>.yaml
    slots/<slot-id>/attempts/<attempt-id>/report.md
    join-receipt.yaml
    merge.md
    proposals/<proposal_id>.yaml
    advocate/<proposal_id>.yaml
  decisions/<decision_id>.yaml
  deliveries/<event_id>/{chat-summary.md,lifecycle.json}
  checkpoints/<10|20>/
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
  under `wave-<n>/slots/<slot-id>/attempts/<attempt-id>/report.md` before synthesis.
- `merger` is the **join barrier**: delegate it once after every slot returns
  or has an explicit terminal failure. Do not start a merger per slot.
- Later waves remain dependency-ordered after the merger, but every independent
  slot inside each later wave uses the same parallel fan-out.
- If a runtime concurrency cap prevents a full fan-out, use the largest
  bounded concurrent batch and mark the run degraded; intentional
  one-at-a-time dispatch is not allowed.

## Wave protocol

1. Use the caller-recorded token mode (`API` or `CURSOR`) and its
   matching billing scope (`API_CREDENTIALS` or `CURSOR_SUBSCRIPTION`).
2. Delegate the first Merger in bootstrap mode with the scenario and initial
   evidence references. Wait for `BOOTSTRAP_WAVE_SPEC` before
   dispatching Wave 1.
3. Before dispatching the first or any later wave, invoke and await the
   mode-specific checker with group `PREFLIGHT` (`fact-slot` for API or `cursor-fact-slot` for CURSOR),
   forward the CapabilityPacket to Merger, and execute the returned
   `ControllerAction`. Merger persists
   `wave-<n>/preflights/<revision_seq>.yaml`. Only READY slots enter fan-out.
4. The default first spec covers **LOGS + CODE + DOCS**. Add **DATA** only
   when the scope actually includes a database or external API contract. When
   the local reference registry is available, Bootstrap selects relevant
   catalogs and adds bounded `BLUEPRINT-SCOUT` slots with explicit
   `CATALOG_ID` values to the same fan-out.
5. A spec has at most **10 slots per wave**, never 10 per group. Each slot has exactly one
   hypothesis/source and one expected fact. A Scout slot returns zero to three
   candidate reference patterns; a `REFERENCE-COVERAGE` slot checks exactly one
   `qualified_pair`. Dispatch all independent slots concurrently. Slots are
   fact collectors: evidence, source anchor, confidence, and missing
   information—no verdicts.
6. After the fan-out join, delegate one post-wave Merger. It accounts for
   every planned logical slot exactly once (one effective terminal attempt),
   writes `join-receipt.yaml`, `merge.md`, evidence ledger, and root graph,
   then emits a Proposal (`proposal_id`, not `decision_id`). The synthesis
   check is not a replacement for Root-depth:
   - What fact changed the leading explanation?
   - What evidence contradicts or weakens it?
   - Which root remains unproven?
   - What single next check most reduces uncertainty?
When Scout packets are present, Merger also qualifies eligible zones and
candidate reference entries, builds sparse `qualified_pairs`, and records
   `coverage_decision` as `REQUIRED`, `OPTIONAL`, or `NOT_NEEDED`. `REQUIRED`
   is allowed only when every qualification predicate is evidenced.
7. The canonical Root-depth questions are (answered against `success_criteria`
   unless `title_only_scope: true`):
   - Is this the final logical status of the answer **for the recorded PASS**?
   - Does this explain the deep root cause (not a label or symptom)?
   - Do we need to dig deeper **to meet `success_criteria`**?
   - What next question would expose another layer (down to API/runtime/language
     semantics if needed)?
8. After every post-wave Merger Proposal, Orchestrator executes
   `CALL_ADVOCATE` once for that `proposal_id` (picker `__MODEL_ADVOCATE__`).
   Do not repeat completed slots. POST_WAVE `NEXT_WAVE_SPEC` at wave 10/20
   authorizes Boss checkpoint evaluation, not dispatch of wave N+1. Wave 21
   is forbidden.
9. **Advocate settlement.** Merger persists `AdvocatePacket` and only then
   mints `decision_id`. Packet must include `success_criteria` and
   `goal_closure`.
   - `END + CLEAN` → deliver the five-part Chat summary.
   - `END + HOLE` material → revised NEXT proposal; immaterial → END +
     recorded rationale, then Chat summary.
   - `NEXT + CLEAN` → accept NEXT (PREFLIGHT next wave, or CALL_BOSS at 10/20,
     or ASK_USER after checkpoint 20).
   - `NEXT + HOLE` → one falsifiable check as a revised NEXT proposal.
   - `HARD_BLOCKER` → exactly one `BLOCKER_RECOVERY` under that
     `proposal_id` (not at wave 20). Capability unchanged → accept
     HARD_BLOCKER and deliver; material new fact → new `proposal_id` +
     Advocate. `devil` returns `AdvocatePacket` only; it does not write
     `loops/**`, spawn slots, decide the outcome, or replace `boss`.
10. After accepted L1 END, call Implementer only when
    `implementation_authorized=true`. Analysis-only requests stay
    `NOT_REQUESTED`. ImplementationReceipt is not product success.
11. Never run a Merger⇄Advocate chat loop. Terminal `END`, confirmed
    HARD_BLOCKER, WAVE_CAP, or ONE_WAVE pause (`wave_result`) must deliver
    Chat summary from the Merger DeliveryPacket; mid-wave stays at one
    status line or silence.

## Evidence routing

Start with direct targeted Read/search. Use logs, docs, and data only when the
question makes them relevant. Use Tenets only when scope remains unknown after
targeted inspection. Use CodeGraph or Octocode only for a structural, caller,
trace, reference, or impact gap; add the other only if that gap persists.
Use Crash for large evidence synthesis or competing hypotheses. Postgres access
remains read-only. Durable memory is the run artifact set, not raw chat history.

## Report canon (5 columns)

| Current behavior | What is broken and why | What to change and how | Validation evidence | Behavior after the change |
|---|---|---|---|---|

- “Current/after” — UI/business meaning + code anchors (module / file:line / symbol).
- Result status: see **part 5) Verdict** below (not harness status).
  - A three-column chat is a compression, not a replacement for the canon in the Chat summary / `findings.md`.

## Chat summary ALWAYS (UNIVERSAL — any `/loop-*` / `/rkx-loop`)

**MUST** deliver the complete result in the USER chat in **English** on the **first** delivery
of a leaf / L1 STOP / phase conclusion / validate verdict / accepted `END` / confirmed
recovery `HARD_BLOCKER` / ONE_WAVE pause / WAVE_CAP.
Merger persists `deliveries/<event_id>/chat-summary.md`; Orchestrator delivers
the DeliveryPacket and writes no files.
`loops/<run>/**` — evidence SoT; **must not** replace the chat with a path to the run.

### Definition of “full Chat summary delivered” (binding)

Count a leaf/result as **delivered** (`milestone chat_itog_delivered`) **only
when the USER chat already contains all 5 parts below in one response**.
A result **without an ASCII diagram**, **without a five-column table**, **without the human-readable
part 5**, or **without citing the run `success_criteria` in both part 1 and
part 5** is **NOT delivered** (contract FAIL) — after that, silent /
“leaf without changes” / “recorded in wave” is not allowed.

Self-check before sending (all ✅ or STOP):

| # | Part | Required? |
|---|---|---|
| 1 | One-sentence business/UI meaning **that quotes `success_criteria`** | ✅ |
| 2 | **Five-column table** (markdown table) | ✅ |
| 3 | Concrete technical facts (path/symbol/conf%) | ✅ |
| 4 | **ASCII / box-drawing flow** (molecule 12) | ✅ |
| 5 | **Human-readable Verdict** — template below (**must quote `success_criteria`**) | ✅ |

Harness/wave metrics (`WAVE_SPEC`, Root-depth, conf%, phase) live in part **3**
and/or `loops/<run>/` — **not** instead of part 5.

**Part 1 binding:** open with the PASS goal in USER language (quote or close
paraphrase of `success_criteria.statement`), then one sentence on whether that
PASS is met / unmet / blocked. A part 1 that answers only a title keyword while
`title_only_scope` is false = FAIL.

### Part 5) Verdict — binding template (for USER, not the harness)

**Required structure:**

```markdown
### 5) Verdict

**✅|❌ <business phrase aligned to success_criteria> — N%**
**Success criteria:** *<exact `success_criteria.statement`>*
**Goal closure:** *product_goal_met=yes|no · question_answered=yes|no · title_only_scope=true|false*
<One sentence explaining what the result means for that PASS; no harness jargon.>
*synthesis: <actual role that assembled the result> · <Model Name actually used> · <wave artifact / validation evidence>*

**How the verification works**

1. <First causal link in a UI, business, data, integration, operations, or regression scenario.>
   **Basis:** *<fact translated into UI/service behavior; include a short technical anchor only when needed>*
   **Where:** *<evidence-id: SLOT-ID / validator / browser / diff> · N% · <Model Name actually used>*

2. <Next causal link; the number of items is arbitrary and determined by the verified chain.>
   **Basis:** *<fact stated in scenario language>*
   **Where:** *<evidence-id> · N% · <Model Name actually used>*

<Continue for as many links as are actually proven. Do not add empty items or replace the chain with an unrelated list of clusters.>

**Tail / blocker:** <only if it actually exists; explain its meaning for the user>.
   **Where:** *<evidence-id> · N% · <Model Name actually used>*
**Advocate:** *<actual model · soft|hard · CLEAN|HOLE|not run; do not present role binding as execution fact>*
```

The number of causal items is unlimited and is not dictated by the example. Each item must have exactly two lines, `Basis` and `Where`. If an item relies on multiple independent facts, list complete triples `evidence-id · N% · model`, separated by `;`, on one `Where` line.

### Soft advisory block `### HOLE — identified gap` (after part 5)

Only for the **SOFT** path (`root >= 96%` with product PASS or title-only
scope) with `ATTACK_STATUS: HOLE`. This is **not**
a sixth required part: `chat_itog_delivered` still requires exactly 5
parts. The block is omitted for soft-`CLEAN`. Hard-`HOLE` follows the hard continuation
mechanism, not this terminal soft block.

Contract (strictly **no more than 2 paragraphs**):

```markdown
### HOLE — identified gap (advisory)

<Paragraph 1: what is unproven and why it does not invalidate the current result ≥96%.>

**SINGLE_NEXT_CHECK:** <one falsifiable check> + UI/business impact. *<evidence-id · N% · model; Advocate · model (role binding)>*
```

Rules:
- More than two paragraphs is forbidden; details → `loops/<run>/`.
- Soft-`HOLE` does not invalidate `≥96%` and does not auto-start the next wave; follow-up
  only on an explicit USER command.
- In part 5, `Advocate:` states `soft · HOLE` without duplicating the block content.

`Basis:` and `Where:` are **bold only as labels**; their content is *italic*. Each fact gets one exact confidence `N%`; ranges, `high`/`medium`/`low`, decimal values, and `NOT_STATED` are forbidden.

**Full canonical example (portable sample — replace names with the active scenario):**

```markdown
### 5) Verdict

**❌ Options are not visible in the assignment dropdown — 94%**
**Success criteria:** *Operators see assignable options in the wizard dropdown so they can complete assignment.*
**Goal closure:** *product_goal_met=no · question_answered=yes · title_only_scope=false*
The UI renders an empty saved candidate list after a sync job failed; a nearby commit is not the cause.
*synthesis: Merger · GPT-5.6 Terra High (role binding) · wave-1 merge / root-graph*
*Execution models were not recorded in the source evidence artifacts; the role binding below is not an execution fact.*

**How the verification works**

1. The assignment screen does not search for options itself; it renders only the saved workspace list.
   **Basis:** *The frontend takes options only from the saved candidate list field; there is no separate source.*
   **Where:** *CODE-1 · 92% · Grok 4.5 High (role binding)*

2. The saved candidate list for this workspace is empty → the dropdown contains only `Unassigned`.
   **Basis:** *Workspace settings for this screen store an empty candidate list.*
   **Where:** *DATA-1 · 96% · Grok 4.5 High (role binding)*

3. This is not a different tenant: the empty list and the assignment target belong to the same workspace.
   **Basis:** *The assignment target, workspace settings, and tenant binding converge on one workspace.*
   **Where:** *DATA-1 · 96% · Grok 4.5 High (role binding)*

4. Eligible people exist elsewhere — an empty dropdown does not mean nobody exists in the system.
   **Basis:** *The directory has eligible members with the required permissions; the connected source has active members.*
   **Where:** *DATA-2 · 96% · Grok 4.5 High (role binding); DATA-3 · 95% · Grok 4.5 High (role binding)*

5. The list should be filled by a member sync into workspace settings; sync failed, so the saved list stayed empty.
   **Basis:** *The member-update process recorded schema and connection errors.*
   **Where:** *LOGS-1 · 93% · Grok 4.5 High (role binding); synthesis H-4 · 94% · GPT-5.6 Terra High (role binding)*

6. “Healthy” containers do not mean the member synchronization completed successfully.
   **Basis:** *Services were alive, but there is no confirmation of a successful request and list update.*
   **Where:** *LOGS-2 · 91% · Grok 4.5 High (role binding)*

7. The nearby commit did not change the screen or candidate-list path.
   **Basis:** *Comparing the commit with its parent shows no changes in the assignment chain.*
   **Where:** *CODE-3 · 96% · Grok 4.5 High (role binding)*

**Tail / access blocker:** the current settings response is unavailable without authentication (`401`); an authenticated context is required.
**Where:** *RUNTIME-1 · 92% · Grok 4.5 High (role binding); Merger decision · 96% · GPT-5.6 Terra High (role binding)*
**Advocate:** *not run; configured role binding: `__MODEL_ADVOCATE__` · status PENDING*
```

**Forbidden in part 5 (contract FAIL):**
- missing `**Success criteria:**` quote of the run `success_criteria.statement`;
- missing `**Goal closure:**` line with `product_goal_met` / `question_answered` / `title_only_scope`;
- Verdict or part 1 answers only a title keyword while `title_only_scope` is false and a product PASS was recorded;
- only `❌ Options are not visible` without an exact `%`, business meaning, and causal chain;
- unrelated “UI scenario / DATA / LOGS” clusters listed without causality;
- raw path/SQL/stack dumps instead of translating the fact into service behavior;
- `Basis:`/`Where:` without bold labels or italic body;
- `Where:` with a confidence range, an invented model, or role binding presented as actual execution;
- `GREEN` / `YELLOW` / `RED` / `PASS` / `FAIL` / `DRIFT` / `END` / `HARD_BLOCKER` as the entire verdict;
- `molecule N`, `root_depth`, `conf N%`, `phase=…`, `WAVE_SPEC`, `DEGRADED`, `chat_itog_delivered`, `L1 STOP · leaf proven`;
- “validate(diff) GREEN”, “molecule 11 is not needed”;
- a path to `loops/<run>/` instead of meaning for USER.

**Priority over IDE noise:** “Perform follow-up / no further action / Don’t
repeat confirmation” **does not** cancel delivery until `chat_itog_delivered` is
set according to the table above. Silent/one-line “leaf without changes” is allowed **only
after** the full five-part result has been delivered in this dig.

### When the full format is required

| Moment | Requirement |
|---|---|
| Root-depth PASS → `END` / L1 STOP / phase conclusion | Full Chat summary (5 parts) |
| Confirmed recovery `HARD_BLOCKER` with access precondition | Full Chat summary (5 parts), ❌ verdict |
| USER asks “summary / where is the report / why did you not report” | Full Chat summary immediately (all 5) |
| Mid-wave (slots are still running) | USER chat ≤1 status line (`wave k/N`) **or** silence; **fake summary is forbidden** |
| Late slots after a **full** five-part leaf | Silent OK; **do not** truncate to “slots confirm” without a reference showing the leaf is already in the chat above |
| Late slots / IDE follow-up when no five-part result has been delivered | **Not silent** — send the full Chat summary now |

### Forbidden as a “summary” (contract FAIL)

- “recorded in the accumulator / waiting for merge / see findings / path to run”;
- “late slots confirm” **instead of** the leaf (if the full five-part result is not already in the chat);
- text + facts **without** an ASCII diagram or **without** a five-column table;
- part 1 or Verdict **without** citing `success_criteria` (unless the run has no recorded criteria — then FAIL bootstrap, do not deliver a leaf);
- only agent id / slots without a business scenario;
- an English-only jargon wall;
- part 5 as harness status instead of ✅/❌ + business phrases;
- postponing the result after complete wave + Root-depth stop;
- treating `chat_itog_delivered` as delivered after an incomplete response “so IDE silence is OK”.

## 17 molecules (binding)

1. **UI/business + code anchors** — module / block / element + business function + code anchor; part 1 quotes `success_criteria`.
2. **Part 5 Verdict:** **✅/❌** + exact `%` + **quoted `success_criteria`** + `goal_closure` line + one business sentence + factual synthesis + arbitrary-length causal chain; each link contains **Basis**/**Where** (evidence-id · exact % · factual model), and the real tail/Advocate is stated when present; **harness jargon is forbidden** instead of the verdict (see Chat summary § Part 5).
3. **Wave Loop Cycle:** bootstrap Merger → parallel groups (**LOGS+CODE+DOCS**, DATA only for DB/API) per `WAVE_SPEC`; post-wave Merger Proposal → Advocate once per `proposal_id` → accepted decision; Boss checkpoints at wave 10/20; deep bug = many narrow slots; Context7/fetch ≥30 for external APIs/libs; micron; e2e; logs+Postgres. Unconditional `N≥3` floor is **not** restored — slot count comes from evidence-backed `WAVE_SPEC` (max 10 per wave).
4. **Deep RC; chat; evidence discipline** — hypotheses are explicitly marked candidates; only evidence from code/PG/logs may be presented as facts. L1 has no product edits until `implementation_authorized`.
5. **MCP stack:** Tenets → Crash (cross-cut) → CodeGraph → Postgres; Octocode on narrow anchors. Evidence-driven, not a fixed sequence.
6. **Success criteria + antipatterns** — mandatory `success_criteria` + `goal_closure` on every run; accepted `END` only when `product_goal_met` (or explicit `title_only_scope`); evidence-first over title keywords; Chat part 1 and Verdict must cite the PASS (see Success criteria §).
7. **Logs-first (inside wave LOGS group):** caller-supplied log source / USER log dump → reverse-proxy access/error when present → application runtime logs → `pnpm logs` / docker logs — top-k, **do not** skip. LOGS-group slots start in the first parallel wave together with DOCS/CODE.
8. **Token economy + slots + retrieval:** models actually selected are recorded at dispatch and in evidence artifacts; `CURSOR-MODELS.md` is policy/binding only, not execution evidence; top-k ~20; full ZZ/log dump is forbidden.
9. **Crash checks + Advocate:** final truth? One `AdvocatePacket` per `proposal_id` (`CLEAN`|`HOLE`); material HOLE is not accepted. Boss is checkpoint-only at waves 10/20.
10. **No workarounds / hardcodes / BP breaks / plan violations** + ponytail YAGNI/reuse.
11. **Revert-first by diff:** if validate(diff) is red — attribution FACT ONLY; our L2 → revert hunks → re-plan; not ours → evidence/STOP; surgical forward only with USER `surgically`/`Smash`.
12. **ASCII / box-drawing** flow diagram in findings/plan/chat (required in Chat summary part 4).
13. **Biz+dev path walk** end-to-end (user scenario + API/UI/logs/PG).
14. **Reviewer stance:** honest and independent; do not criticize for criticism’s sake.
15. **Startup lens** optional (`--lens startup`).
16. **Validate edits explicitly** — after L2, validate(diff) is mandatory in full.
17. **Consistency:** after editing plan/skills/rules — todos↔body↔mermaid↔atoms↔ADR/sources/tiers; FAIL → edit the doc.

Wave artifacts and Root-depth answers remain mandatory internal evidence. They
do **not** replace Chat summary. Do not replace the canonical Root-depth questions
with an arbitrary questionnaire.

## Easy summary artifact

At a terminal Cursor `stop` event, the project hook
`.cursor/hooks/rkx_write_easy_summary.py` looks up the terminal
lifecycle event for the current conversation by exact event id and writes a compact
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
   (`.cursor/hooks.json` → `.cursor/hooks/rkx-slack-notify.sh`) reads the
   exact lifecycle event at
   `loops/<run>/deliveries/<event_id>/lifecycle.json` from
   `state/current.yaml` (`pending_delivery_event_id` / `delivery_ref`),
   matches the current `conversation_id`, and posts via Incoming Webhook or
   `chat.postMessage` only when the user must answer or decide
   (`waiting_user`, `blocked`, `failed`, `wave_cap`). Legacy single-file
   `slack-notification.json` is readable only when no exact event pointer
   exists.
2. **Result card:** the same hook posts exactly once for a completed loop
   (`completed`) and labels it `Work summary`. ONE_WAVE pause uses
   `wave_result` (chat only, no Slack).
3. **Full verdict:** after the complete Chat summary is delivered in Cursor, the
   orchestrator may send one separate full verdict via
   `plugin-slack-slack` / `slack_send_message`. The full verdict keeps the
   canonical five-part format and is never reconstructed from
   `state/current.yaml` prose. Hook and MCP ownership must not send the same
   class twice.

`started` and `progress` remain valid lifecycle artifacts for auditability but
are not sent to Slack. Common writer mistakes (`kind=attention|result`) are
auto-normalized by the hook. The notifier selects by exact event id, never by
mtime. New artifacts must carry the exact active
`conversation_id` and a `notification_type` of `attention` or `result`;
placeholder IDs are invalid. Older artifacts without `notification_type` are
classified from `kind` for compatibility. The hook selects the newest sendable
artifact, claims its event under an exclusive short lease, retries outbound
Slack POSTs, and retains a successful delivery record for at least the
artifact-age window. A process failure after external delivery may still permit
one bounded retry because an Incoming Webhook offers no idempotency key.
Missing/mismatched artifacts and Slack failures remain fail-open but are
appended to `~/.cursor/rkx-slack-notify.log`. When the transport is a channel
Incoming Webhook, `SLACK_NOTIFY_MENTION` addresses the configured recipient so
Slack can generate a mobile push; the value belongs only in
`~/.cursor/rkx-slack-notify.env`.

**Lifecycle artifact contract:**

```json
{
  "schema_version": 1,
  "conversation_id": "cursor-conversation-id",
  "event_id": "unique-lifecycle-event",
  "run_id": "2026-08-07-rkx-example",
  "phase_id": "phase-1",
  "wave_id": 1,
  "kind": "waiting_user",
  "notification_type": "attention",
  "waiting_reason": "USER_SCOPE",
  "correlation_id": "corr-1",
  "problem_title": "Options are not visible in the assignment wizard dropdown at step 3",
  "success_criteria": "Operators see assignable options in the wizard dropdown so they can complete assignment",
  "summary": "The product UI shows an empty list because saved workspace settings did not receive candidates from the sync source.",
  "blocker": "The check hit 401 because authentication was missing.",
  "next_action": "Open an authenticated Browser Tab and repeat the read-only check.",
  "capture_dir": "rkx_capture_2026-08-08",
  "decision_artifact": {
    "path": "loops/2026-08-07-rkx-example/wave-1/merge.md",
    "sha256": "artifact digest"
  },
  "full_verdict_available": false
}
```

`problem_title` preserves the original user scenario, not an
unconfirmed hypothesis. Optional `success_criteria` echo may repeat the PASS
in safe short form. `summary`, `blocker`, and `next_action` must be
understandable without RKX knowledge. Do not write tokens, secrets, raw slot
transcripts, PII without necessity, or the full Chat summary into the artifact.

**Lifecycle card (EN):**

```text
<status> <detailed problem title>

<what this means for the user>
Blocker: <only if present>
Next step: <one concrete action>

<run> · <wave>
```

Percentages, evidence, and actual models are shown only in the full verdict,
if they are actually recorded in evidence artifacts. A working link to the
full result may be added as a normal Markdown link; interactive
`Continue checking` / `Stop` require a separate callback/backend and are not
shown as dead buttons.

Phone delivery = Slack mobile app push for that DM/channel. Credentials live
only in `~/.cursor/rkx-slack-notify.env` (never in git).
