# RKX Loop — Blueprint Scout & Coverage Flow

> Status: active Cursor control-plane design; runtime picker/model availability
> and operational QA are checked separately.
>
> Existing roles: `rkx-loop` orchestrator, `merger`, `fact-slot` /
> `cursor-fact-slot`, `blueprint-scout` / `cursor-blueprint-scout`, `devil`
> (Advocate), `implementer`.
>
> Catalog registry: `${CONTROL_PLANE_ROOT}/reference/blueprint-index.yaml`.
> Generic snapshot: `${CONTROL_PLANE_ROOT}/reference/system-design-primer/`.
> Telephony catalog: `${CONTROL_PLANE_ROOT}/reference/telephony/catalog.yaml`.
> This document describes the active contract; the files under `${CONTROL_PLANE_ROOT}/agents`,
> `${CONTROL_PLANE_ROOT}/skills` and `${CONTROL_PLANE_ROOT}/rules` remain the runtime source of truth.

`REFERENCE CATALOG` — a pinned local registry of source-backed entries.
`REFERENCE ENTRY` — one normalized architecture, protocol profile, call flow,
deployment, interconnection rule, invariant, trade-off or failure mode. System
Design Primer, IETF RFCs, SIPconnect and 3GPP/IMS are separate catalogs; none
is an automatic project coding standard.

## 1. One-screen diagram

```text
USER: problem X + /rkx-loop
        │
        ▼
ORCHESTRATOR
  asks API/Cursor
  stores problem_title + conversation_id
        │
        ▼
MERGER: BOOTSTRAP
  creates manifest
  forms initial hypotheses
  returns BOOTSTRAP_WAVE_SPEC
        │
        ▼
WAVE 1 — one parallel fan-out
        │
        ├── LOGS slots
        ├── CODE slots
        ├── DOCS slots
        ├── DATA slots, if there is DB/API scope
        └── BLUEPRINT-SCOUT
              ├── receives the problem and initial hypotheses
              ├── selects catalog_id and reads the reference catalog
              └── returns candidates and links
        │
        ▼
JOIN → MERGER: POST-WAVE
  combines actual facts and Scout feedback
  qualifies:
    ├── eligible_zones
    ├── qualified_references
    └── sparse qualified_pairs
        │
        ▼
ADVOCATE — dual-mode for the post-wave decision_id
  first: root >= 96%?
        │
        ├── soft (>=96%): advisory; CLEAN → Chat summary; HOLE → block without auto-next
        └── hard (<96%): gate; CLEAN/HOLE/BLOCKER_RECOVERY as before
        │
        ▼
REFERENCE-COVERAGE WAVE, if needed
  qualified_pairs only, after relevance/applicability/causal/impact gates
  one narrow check for each qualified pair
  all independent pairs in parallel
        │
        ▼
JOIN → MERGER → DUAL ADVOCATE → NEXT / END / BLOCKER
        │
        ▼
L1 STOP → Chat summary ALWAYS → USER gate
        │
        ├── `Smash`
        │       → implementer → Build / validate(diff)
        │
        └── «Ship» / «Build docker»
                → only after green diff validation
```

## 2. Qualification gate before coverage

Scout candidates are not automatically coverage targets. Merger builds
`qualified_pairs` instead of dispatching the full candidate-zone Cartesian
product.

```text
qualified_pair =
  zone_relevance >= 70%
  AND reference_applicability >= 70%
  AND blueprint_applicability >= 70% when the legacy alias is present
  AND relation ∈ {root_zone, causal_predecessor}
  AND verification_target ∈
      {invariant, contract, failure_mode, flow_transition,
       protocol_requirement, deployment_boundary,
       reference_architecture, interconnection_contract}
  AND impact_targets intersects
      {root_hypothesis, remediation_plan, root_confidence}
  AND every percentage has evidence + CONFIDENCE_BASIS
```

```text
coverage_decision:
  REQUIRED     → at least one qualified pair can change root/plan/confidence
  OPTIONAL     → reference is relevant but cannot change this investigation
  NOT_NEEDED   → no pair passes the qualification predicate
  NOT_EVALUATED → Bootstrap has not merged Scout evidence yet
```

`coverage_required: true` is valid only for `REQUIRED`. A declared
`coverage_budget` limits the dispatch. Budget overflow requires explicit Merger
triage or marked degraded batches; no qualified pair may be silently dropped.

## 3. Detailed flow from the first message

### 3.1. USER starts the loop

```text
┌──────────────────────────────────────────────────────────────────────┐
│ USER                                                                 │
│                                                                      │
│ Message:  “We have problem X”                                       │
│ Command:  /rkx-loop <scenario or symptom>                          │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                                         │
│                                                                      │
│ 1. Asks for token mode: API or Cursor                               │
│ 2. Preserves the original problem_title without replacing it with a  │
│    root hypothesis                                                    │
│ 3. Preserves the current conversation_id                              │
│ 4. Delegates Merger in BOOTSTRAP mode                                │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
```

Advocate is not invoked at this stage. Bootstrap plans the first wave; it is
not a post-wave decision.

### 3.2. MERGER: BOOTSTRAP

```text
┌──────────────────────────────────────────────────────────────────────┐
│ MERGER: BOOTSTRAP                                                   │
│                                                                      │
│ Receives:                                                            │
│   - problem_title                                                    │
│   - initial evidence references                                      │
│   - token mode                                                       │
│                                                                      │
│ Does:                                                                │
│   - creates a manifest                                                │
│   - forms evidence-backed hypotheses                                  │
│   - identifies narrow sources and expected facts                      │
│   - adds BLUEPRINT-SCOUT to WAVE-1 when a catalog is available         │
│                                                                      │
│ Returns: BOOTSTRAP_WAVE_SPEC                                        │
│ Does not:                                                            │
│   - invoke Advocate                                                   │
│   - launch slots itself                                               │
│   - create a diagnosis from an assumption                             │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
```

`Merger` must add Scout to `WAVE_SPEC` itself; the orchestrator does not invent
slots after receiving the spec. Scout receives only the initial hypotheses and
candidate zones. The root is not yet proven in the first wave.

### 3.3. WAVE 1: initial facts and early Scout

All independent slots launch in one parallel fan-out. The groups here are scope
labels, not sequential stages.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ WAVE 1 — PARALLEL FAN-OUT                                           │
│                                                                      │
│ ┌────────────────┐  ┌────────────────┐  ┌────────────────┐          │
│ │ LOGS           │  │ CODE           │  │ DOCS           │          │
│ │ facts from logs │  │ facts from code │  │ docs/contracts  │          │
│ └────────────────┘  └────────────────┘  └────────────────┘          │
│                                                                      │
│ ┌────────────────┐  ┌─────────────────────────────────────────────┐ │
│ │ DATA           │  │ BLUEPRINT-SCOUT                              │ │
│ │ DB/API only    │  │ early reference-candidate search               │ │
│ └────────────────┘  └─────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

#### What BLUEPRINT-SCOUT receives

```text
TASK:
  find reference candidates relevant to the problem and initial hypotheses

SCOPE:
  - problem_title
  - hypothesis_id
  - candidate zone / file / symbol / contract
  - open question
  - reference catalog id selected by Merger
  - normalized catalog registry and selected catalog index
  - exact pinned local source refs

CATALOG:
  registry: ${CONTROL_PLANE_ROOT}/reference/blueprint-index.yaml
  problem_domain: <registry domain tag>
  catalog_id: system-design | telephony
  index: <selected catalog index>
  root: <selected local catalog root>
```

#### What BLUEPRINT-SCOUT returns

```text
BLUEPRINT_CANDIDATE:
  blueprint_id: <stable id>
  reference_id: <canonical stable reference id>
  catalog_id: <system-design | telephony>
  reference_type: <reference_architecture | call_flow | deployment_architecture | protocol_profile | interconnection_specification | legacy pattern type>
  authority: <IETF | SIP Forum | 3GPP | catalog source>
  source: <exact local index/source anchor at catalog_revision>
  scope: <normative | industry_profile | reference_architecture | informative>
  related_hypothesis: <H-id>
  related_zone: <zone-id or code anchor>
  applicability: <0%–100%>
  relation: root_zone | causal_predecessor | unrelated | unknown
  verification_targets: invariant | contract | failure_mode | flow_transition | protocol_requirement | deployment_boundary | reference_architecture | interconnection_contract
  expected_evidence: <one concrete trace/config/code/runtime observation>
  why_relevant: <short evidence-backed reason>
  unknowns: <what cannot be confirmed in this slot>
  evidence: <source anchor + code/problem anchor>
  confidence: <0%–100%>
  confidence_basis: <why>
```

Scout does not:

- declare a reference entry mandatory;
- prove the root cause;
- compare the entire codebase with the catalog;
- decide `END`, `NEXT_WAVE_SPEC`, or `HARD_BLOCKER`;
- write shared wave artifacts;
- replace LOGS/CODE/DOCS facts.

### 3.4. JOIN and MERGER: POST-WAVE

After all slots return, the orchestrator waits at the join barrier and delegates
exactly one post-wave Merger.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ JOIN                                                                 │
│                                                                      │
│ All slot packets returned or received an explicit terminal failure.    │
│ Merger first saves each packet separately:                             │
│ loops/<run>/wave-1/slots/<slot-id>/report.md                        │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│ MERGER: POST-WAVE #1                                                │
│                                                                      │
│ 1. Writes merge.md, state.md, root-graph.md, ledger.md                │
│ 2. Combines LOGS/CODE/DOCS/DATA and BLUEPRINT-SCOUT feedback           │
│ 3. Runs the synthesis check                                            │
│ 4. Answers the canonical Root-depth questions                          │
│ 5. Records root anchors and actually affected zones                    │
│ 6. Qualifies eligible zones, patterns, and sparse qualified_pairs       │
│ 7. Accepts coverage_decision: REQUIRED / OPTIONAL / NOT_NEEDED          │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
```

Merger selects one path:

```text
┌─────────────────────────────────────────────┐
│ BLUEPRINT DECISION                          │
└─────────────────────┬───────────────────────┘
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
  NOT_NEEDED       OPTIONAL       REQUIRED
  no qualified     reference       qualified_pairs
  pair             without wave    after predicate
```

Merger's decision is first checked against `root confidence`: soft at `>=96%`,
hard at `<96%`.

### 3.5. DUAL ADVOCATE after the first wave

```text
┌──────────────────────────────────────────────────────────────────────┐
│ POST-WAVE MERGER                                                     │
│ STEP 1: root >= 96% + Root-depth?                                    │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │ >=96%              │ <96%               │
              ▼                    ▼                    │
        SOFT ADVOCATE         HARD ADVOCATE             │
              │                    │                    │
        CLEAN → Chat summary   CLEAN → NEXT fan-out        │
        HOLE  → Chat summary   HOLE  → one next-check      │
                + HOLE block HARD_BLOCKER → recovery    │
                (no auto-next)                          │
```

Advocate returns only `ATTACK_PACKET`. It is not Scout, does not choose an
outcome, create slots, or write artifacts. Soft does not replace hard.

```text
SOFT CLEAN → final Chat summary
SOFT HOLE  → Chat summary + advisory HOLE block (max 2 paragraphs); no auto-next
HARD CLEAN + NORMAL_GAP / REQUIRED → dispatch gaps or REFERENCE-COVERAGE
HARD HOLE  → one falsifiable SINGLE_NEXT_CHECK
HARD_BLOCKER → one BLOCKER_RECOVERY; no second Advocate for the same decision_id
```

### 3.6. REFERENCE-COVERAGE WAVE

This wave launches only if Merger formed
`coverage_decision: REQUIRED`, `coverage_required: true`, the qualified pairs
passed all qualification predicates, and Advocate passed this decision through
`CLEAN`.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ REFERENCE-COVERAGE WAVE                                             │
│                                                                      │
│ Dispatch set: qualified_pairs                                         │
│ Not the full zones × catalog entries Cartesian product                 │
│                                                                      │
│ ┌─────────────────────┐  ┌─────────────────────┐                    │
│ │ QUALIFIED-PAIR-1    │  │ QUALIFIED-PAIR-2    │                    │
│ │ one narrow slot     │  │ one narrow slot     │                    │
│ └─────────────────────┘  └─────────────────────┘                    │
│                                                                      │
│ ┌─────────────────────┐  ┌─────────────────────┐                    │
│ │ QUALIFIED-PAIR-3    │  │ QUALIFIED-PAIR-4    │                    │
│ │ one narrow slot     │  │ one narrow slot     │                    │
│ └─────────────────────┘  └─────────────────────┘                    │
│                                                                      │
│ All independent pairs launch in parallel.                             │
│ Non-applicability is recorded explicitly, not by deleting the pair.    │
└──────────────────────────────────────────────────────────────────────┘
```

#### Contract for one coverage slot

```text
INPUT:
  zone:
    zone_id: <id>
    code_refs: [file:symbol:lines]
    contract: <if present>
  reference:
    blueprint_id: <id or compatibility alias>
    reference_id: <canonical id>
    catalog_id: <system-design | telephony>
    reference_type: <entry type>
    source_refs: [catalog:file#section]
  expected_fact:
    compare one specific invariant / contract / flow state / failure behavior

OUTPUT:
  zone_id: <id>
  blueprint_id: <id>
  reference_id: <canonical id>
  catalog_id: <catalog id>
  reference_type: <entry type>
  status: MATCH | DEVIATION | NOT_APPLICABLE | UNKNOWN
  code_evidence: [<exact code anchors>]
  reference_evidence: [<exact catalog anchors>]
  meaning_for_problem: <connection to the original scenario>
  confidence: <0%–100%>
  confidence_basis: <why>
  missing_evidence: <if UNKNOWN>
```

`DEVIATION` does not automatically mean “error.” Merger must determine whether
the difference is:

```text
an acceptable adaptation
        or
an architectural gap
        or
an irrelevant difference from the reference entry
```

### 3.7. JOIN after coverage and the next Advocate

```text
REFERENCE-COVERAGE slots
        │
        ▼
JOIN
        │
        ▼
MERGER: POST-WAVE
  - saves each comparison report
  - verifies that qualified_pairs coverage is closed
  - does not leave any qualified pairs unprocessed
  - links deviations to the original problem
  - updates the root graph and ledger
        │
        ▼
ADVOCATE: new decision_id
  - verifies the coverage result
  - verifies the causal link from deviation → problem
  - challenges cargo-cult conclusions
        │
        ▼
NEXT_WAVE_SPEC / END / HARD_BLOCKER
```

This is a new post-wave decision, so it requires a new `decision_id` and exactly
one new Advocate pass. Do not use a second Advocate for the first wave's
`decision_id`.

## 4. Dual Advocate gate (soft ≥96% / hard <96%)

Advocate is not launched:

- during Bootstrap;
- after each individual slot;
- as part of Scout;
- after `BLOCKER_RECOVERY`.

After post-wave Merger, check `root confidence` first:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ POST-WAVE MERGER DECISION                                            │
│ STEP 1: root >= 96% ?                                                │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │ >=96%                  │ <96%                   │
          ▼                        ▼                        │
       SOFT AUDIT               HARD GATE                   │
          │                        │                        │
   CLEAN → Chat summary        CLEAN → NEXT fan-out            │
   HOLE  → Chat summary        HOLE  → one next-check          │
           + HOLE block     HARD_BLOCKER → recovery         │
           (no auto-next)                                   │
```

Soft does not replace hard. Merger makes the factual decision, the orchestrator
controls dispatch and mode, and Advocate returns only `ATTACK_PACKET`.

## 5. When the loop ends

```text
┌──────────────────────────────────────────────────────────────────────┐
│ ACCEPTED END                                                         │
│                                                                      │
│ Allowed only if:                                                     │
│   - root confidence ≥ 96%                                            │
│   - Root-depth gate PASS                                             │
│   - the deep root cause is explained                                  │
│   - all required evidence gaps are closed                             │
│   - qualified_pairs coverage is closed if the REQUIRED phase ran       │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
```

### 5.1. Required Chat summary

On `END`, a confirmed recovery blocker, L1 STOP, or phase completion, the
orchestrator delivers one complete English Chat summary:

```text
1. Business/UI meaning in one sentence
2. A five-column table
3. Concrete technical facts: paths, symbols, evidence, confidence
4. An ASCII / box-drawing diagram
5. A human-readable ✅/❌ Verdict
   - a causal chain
   - **Basis:** *...*
   - **Where:** *evidence-id · exact % · factual model*
```

`loops/<run>/` stores the evidence SoT but does not replace this Chat summary.

### 5.2. L1 → L2 after an explicit USER gate

```text
L1 evidence / plan / validate_plan
        │
        ▼
L1 STOP
        │
        ▼
USER explicitly writes:
  `Smash`
        │
        ▼
IMPLEMENTER
  receives the approved scope and plan
  does not revisit the root
  does not launch new checker slots
        │
        ▼
BUILD / VALIDATE_DIFF
        │
        ├── red
        │     → attribution FACT ONLY
        │     → re-plan / revert-first under the rules
        │
        └── green
              → result ready
```

Docker does not follow from an ordinary `Build`:

```text
«Ship» / «Build docker»
  → only after green validate(diff)
  → pnpm build:compose
```

## 6. Side-channel lifecycle

This is not part of the evidence chain, but it is part of the operational flow:

```text
significant lifecycle transition
        │
        ▼
Merger updates:
loops/<run>/slack-notification.json
        │
        ▼
stop-hook sends the lifecycle card
        │
        ▼
after the Chat summary is actually delivered
orchestrator may send one full verdict through Slack MCP
```

The lifecycle card does not build the root from the global `state.md` and does
not replace Chat summary.

## 7. Responsibility boundaries

```text
USER
  states the problem and provides the L2 gate

ORCHESTRATOR
  asks for token mode
  dispatches the spec
  waits for the join
  checks 96% FIRST
  launches the soft or hard Advocate
  accepts the process's technical outcome

MERGER
  builds hypotheses
  saves slot reports
  synthesizes evidence
  selects catalogs and qualifies zones/references/pairs
  selects REQUIRED / OPTIONAL / NOT_NEEDED
  returns NEXT / END / HARD_BLOCKER

FACT-SLOT
  checks one narrow source or hypothesis
  returns a fact and evidence
  does not diagnose

BLUEPRINT-SCOUT
  selects reference candidates in the specified catalog_id
  returns sources and applicability
  does not prove the root or launch coverage

REFERENCE-COVERAGE SLOT
  compares one qualified pair zone × reference entry
  returns MATCH / DEVIATION / NOT_APPLICABLE / UNKNOWN

ADVOCATE / DEVIL
  dual-mode: soft ≥96% (advisory) / hard <96% (gate)
  returns ATTACK_PACKET
  does not write artifacts, launch slots, or decide END
  soft does not replace hard

IMPLEMENTER
  writes product code only after an explicit USER gate
  works only within the approved scope
```

## 8. Main principle

```text
Scout searches for possible reference entries.
Merger selects a catalog and qualifies only causal and impact-relevant pairs.
Check root >= 96% first: soft audit on success, hard gate below 96%.
Coverage slots compare only qualified_pairs.
Merger links a difference from a reference to the root cause only through local
facts.
```

A reference entry is a verifiable norm or model, not an automatic project
standard. A difference from the System Design Primer, IETF, SIPconnect, or IMS
becomes a problem only when it is proven to be connected to the original user
scenario, contract, or failure mode.
