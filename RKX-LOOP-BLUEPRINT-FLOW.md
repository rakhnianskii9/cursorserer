# RKX Loop — canonical control-plane topology

Status: `CANONICAL_IMPLEMENTED` (active contracts, scenario tests, exact-event
notification path, and canonical-run validation are aligned).

This file is the portable source of truth for topology, ownership, and state
transitions. A contract change is accepted only together with matching schemas,
fixtures, and scenario/runtime validation.

Public files in this archive are English. User-facing chat language is owned by
the installing workspace, not by these files.

## 1. Control-plane shape

### 1.1 Machine contracts

Closed schemas exist for:
`RequestEnvelope`, `WaveSpec`, `CapabilityPacket`, `PreflightDecision`,
`ControllerAction`, `SlotReport`, `SlotReceipt`, `DispatchReceipt`,
`JoinReceipt`, `Proposal`, `AdvocatePacket`, `BossPacket`, `AcceptedDecision`,
`CurrentState`, `DeliveryPacket`, `LifecycleEvent`, `ImplementationRequest`,
and `ImplementationReceipt`.

- `proposal_id` exists before the gate; `decision_id` appears only after an
  accepted decision.
- Controlling **decisions** are exactly three:
  `NEXT_WAVE_SPEC | END | HARD_BLOCKER`.
- Controlling **runtime actions** are the closed `ControllerAction.action`
  enum. Decision ≠ action. The orchestrator executes only a ControllerAction.
- `decision_kind` and open status enums are absent from the control loop.
  Domain conclusions live in `finding_kind` and do not drive transitions.
- Capability observation is separate from Merger decisions:
  `READY | UNAVAILABLE | STALE | INVALID` are not transition actions.
- Every packet carries `run_id`, `phase_id`, `wave_id`, `spec_revision`,
  `correlation_id`, and the parent artifact identity.

### 1.2 Write ownership

- Orchestrator is `readonly: true`. It does not write preflight, Advocate,
  Boss, summary, or lifecycle artifacts.
- Checker/Scout writes only the write-once
  `slots/<slot-id>/attempts/<attempt-id>/report.md` and returns a `SlotReceipt`
  with path/hash/`attempt_id`. The logical slot stays one; attempt identity is
  unique. A late receipt with a foreign `attempt_id` does not join.
- Merger is the only writer of shared run/wave artifacts: manifest,
  `wave-<n>/specs/<revision_seq>.yaml`, `wave-<n>/preflights/<revision_seq>.yaml`,
  join, ledger, root graph, proposal, Advocate/Boss packets, accepted
  decision, current state, delivery, and lifecycle event. CAS: writing
  `state/current.yaml` is allowed only when
  `current.state_revision == ControllerAction.expected_state_revision`.
  Otherwise `STALE_TRANSITION`.
- Advocate and Boss are readonly: they return packets to Merger and do not
  create decisions or waves.
- Implementer writes only approved product changes and its own immutable
  implementation report.

### 1.3 Executor routing

- Active routes are `API | CURSOR` only. CODEX is absent from routing.
- Executor choice does not change schema, ownership, or wave semantics.
- Historical CODEX mentions belong only in explicitly archival documents.

### 1.4 Wave engine

- Fan-out is one parallel batch; dependent checks go to the next wave.
- The slot limit is **per wave**, not per group; max 10.
- `max_slot_attempts` is set on WaveSpec. Transport failure is not a semantic
  Orchestrator decision. Redispatch uses the same `slot_id` with a new
  `attempt_id` and a new write-once path.
- After every wave: join → Merger proposal → Advocate → accepted decision.
- A POST_WAVE `NEXT_WAVE_SPEC` at wave 10/20 does **not** authorize dispatch
  of wave N+1; it enters the Boss checkpoint (`route_action=CALL_BOSS`).
- No `END`/`HARD_BLOCKER` after wave 10 → Boss checkpoint 10 → Merger
  re-synthesis → Advocate; `NEXT_WAVE_SPEC` after that checkpoint opens
  waves 11–20.
- After wave 20 without a terminal → final Boss → final Merger → Advocate;
  wave 21 does not start. `NEXT_WAVE_SPEC` after checkpoint 20 → `ASK_USER`
  / `WAVE_CAP`.
- An unresolved final checkpoint → `WAITING_USER` / `WAVE_CAP` plus Slack
  `attention`.

### 1.5 L1 and L2

- `RequestEnvelope.implementation_authorized` records whether the original
  request already authorized product changes.
- `L1 END` means investigation and implementation scope are complete; the
  product is not yet changed.
- When `implementation_authorized=true`, after L1 END the Orchestrator calls
  Implementer without a second permission prompt.
- Analysis-only requests never call Implementer; status is `NOT_REQUESTED`.
- `ImplementationReceipt` ≠ product success. Merger validates the receipt /
  validation slots and only then records the implementation result.
- After `VALIDATED` / `FAILED`, Merger writes a terminal LifecycleEvent plus
  DeliveryPacket (`product=MET` or `NOT_MET`) and Orchestrator delivers to the
  user.
- New evidence after implementation opens a new `phase_id`; the accepted L1
  decision is not rewritten.

### 1.6 Filesystem and resume

- `run_id` equals the `loops/<run_id>/` folder name; aliases are forbidden.
- Canonical current pointer is `state/current.yaml`. For new runs,
  `latest-decision.*` is not authoritative.
- Resume from `state/current.yaml`: `pending_action` and `awaiting_input`;
  mtime search is forbidden. `pending_action` is a `ControllerAction.action`
  or `NONE`. After delivering a question: `pending_action=NONE`,
  `awaiting_input=USER`. `action_id` is the idempotency key; resume reissues
  the same id until `last_applied_action_id` matches.
- Shared-state writes are append/write-once revisioned paths plus a CAS
  update of the current pointer (`state_revision`, `previous_state_revision`,
  `previous_state_sha256`).
- WaveSpec/preflight are never overwritten: REPLAN writes
  `specs/0002.yaml` / `preflights/0002.yaml`; current points at the active
  revision.
- Legacy runs do not redefine current contracts without a migration adapter.

### 1.7 Delivery and Slack

- Merger forms the Chat summary and the immutable lifecycle event after an
  accepted result or `WAITING_USER`.
- Orchestrator only delivers a ready DeliveryPacket to chat.
- The notifier reads an exact lifecycle event ref/id; it does not pick an
  artifact by mtime.
- `WAVE_CAP` requires `attention`.
- A notifier error does not change run state and does not start a wave.

### 1.8 Runtime validation

- Fixtures and real
  `loops/<run>/wave-*/specs|preflights|proposals|join-receipt` plus
  `decisions/` are validated.
- Checks include: folder name ≡ `run_id`, parent revisions, unique IDs,
  complete join of required slots, legal state transitions, writer ownership.
- Scenario coverage includes normal END, slot timeout, stale preflight,
  checkpoint 10/20, Slack wave-cap, explicit L2, analysis-only L1,
  implementation failure, and resume.

## 2. Diagram legend

```text
  ───>  call / handoff without a write
  ~~~>  return of a structured packet
  [SLOT-WRITE]    slot writes only its own immutable report
  [MERGER-WRITE]  Merger writes shared run/wave state and decisions
  [IMPL-WRITE]    Implementer writes the approved product diff and its report
  [ ? ]           semantic fork that only Merger may decide
  ╳               forbidden edge
```

## 3. Executable topology

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ 0. USER REQUEST                                                              │
│                                                                              │
│ intent + scope + optional resume_run_id + executor_mode                      │
│                                                                              │
│ continuation_policy:                                                         │
│   ONE_WAVE       one completed wave, then pause/summary                      │
│   CONTINUOUS     continue until END / HARD_BLOCKER / WAVE_CAP                │
│                                                                              │
│ implementation_authorized:                                                   │
│   TRUE   original request already requires a fix/implement/change            │
│   FALSE  original request is analysis only                                   │
│                                                                              │
│ executor_mode: API | CURSOR                                                  │
│ CODEX is absent from the active route                                        │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                v
┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. ORCHESTRATOR — READONLY DISPATCH / DELIVERY                               │
│                                                                              │
│ Does:                                                                        │
│   - normalize RequestEnvelope                                                │
│   - execute exactly the ControllerAction Merger returned                     │
│   - start independent slots in one parallel batch                            │
│   - wait for returns and form a transport-only DispatchReceipt               │
│   - forward packets to Merger                                                │
│   - deliver a ready DeliveryPacket to the user                               │
│                                                                              │
│ Does not:                                                                    │
│   ╳ write any run/product file                                               │
│   ╳ create hypotheses/spec/preflight/proposal/decision/summary               │
│   ╳ choose END/NEXT/BLOCKER                                                  │
│   ╳ treat timeout as evidence                                                │
│   ╳ call Implementer without implementation_authorized                       │
│                                                                              │
│ RequestEnvelope:                                                             │
│   run_id? | resume_run_id? | conversation_id | intent | scope                │
│   executor_mode | continuation_policy                                        │
│   implementation_authorized | correlation_id                                 │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ bootstrap | resume | user_response
                                v
┌──────────────────────────────────────────────────────────────────────────────┐
│ 2. MERGER / RUN CONTROLLER — SHARED-STATE OWNER                              │
│                                                                              │
│ [run_id supplied?]                                                           │
│   ├─ NO                                                                      │
│   │   └─ create run_id == folder name                                        │
│   │      [MERGER-WRITE] loops/<run_id>/manifest.yaml                         │
│   │      [MERGER-WRITE] loops/<run_id>/events/0001-run-created.yaml          │
│   │      [MERGER-WRITE] loops/<run_id>/state/current.yaml                    │
│   │                                                                          │
│   └─ YES                                                                     │
│       └─ load exactly state/current.yaml                                     │
│          [resume action matches pending_action?]                             │
│          ├─ NO  ~~~> ControllerAction: EXPLAIN_INVALID_RESUME                │
│          └─ YES ──> continue the recorded transition only                    │
│                                                                              │
│ [scenario/scope sufficient?]                                                 │
│   ├─ NO  ──> state WAITING_USER ~~~> ControllerAction: ASK_USER              │
│   └─ YES                                                                     │
│       └─ evidence-backed hypotheses                                          │
│          [MERGER-WRITE] hypotheses/<revision>.yaml                           │
│          [MERGER-WRITE] wave-<n>/specs/<revision_seq>.yaml                   │
│          ~~~> ControllerAction: PREFLIGHT                                    │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ WaveSpec
                                v
┌──────────────────────────────────────────────────────────────────────────────┐
│ 3. CAPABILITY PREFLIGHT                                                      │
│                                                                              │
│ Orchestrator ───> mode-specific preflight executor                           │
│ executor ~~~> CapabilityPacket                                               │
│ Orchestrator ───> Merger CapabilityPacket                                    │
│                                                                              │
│ CapabilityPacket per slot:                                                   │
│   READY | UNAVAILABLE | STALE | INVALID                                      │
│                                                                              │
│ Merger checks the exact spec_revision and the full planned slot set          │
│ [MERGER-WRITE] wave-<n>/preflights/<revision_seq>.yaml                       │
│ CAS: expected_state_revision must match current.state_revision               │
│                                                                              │
│ [Merger PreflightDecision]                                                   │
│   ├─ DISPATCH                                                                │
│   │    every REQUIRED slot is executable; OPTIONAL is ready or skipped       │
│   │    ~~~> ControllerAction: DISPATCH_WAVE                                  │
│   │                                                                          │
│   ├─ REPLAN                                                                  │
│   │    scope/revision/required source is stale                               │
│   │    [MERGER-WRITE] wave-<n>/specs/<revision_seq+1>.yaml                   │
│   │    ~~~> ControllerAction: PREFLIGHT                                      │
│   │                                                                          │
│   ├─ WAITING_USER                                                            │
│   │    continuation needs an external user choice                            │
│   │    [MERGER-WRITE] awaiting_input=USER, pending_action=NONE               │
│   │    ~~~> ControllerAction: ASK_USER (once per action_id)                  │
│   │                                                                          │
│   └─ HARD_BLOCKER_CANDIDATE                                                  │
│        required evidence is unreachable with no falsifiable substitute       │
│        ~~~> ControllerAction: CALL_ADVOCATE (blocker proposal)               │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ ControllerAction: DISPATCH_WAVE
                                v
┌──────────────────────────────────────────────────────────────────────────────┐
│ 4. WAVE N — ONE PARALLEL FAN-OUT                                             │
│                                                                              │
│                              WaveSpec                                        │
│                                 │                                            │
│       ┌───────────────┬─────────┼─────────┬───────────────┐                  │
│       v               v         v         v               v                  │
│   LOGS slots      CODE slots  DOCS slots DATA slots   BLUEPRINT/REFERENCE    │
│                                          only if scope  ordinary slots       │
│                                                                              │
│ All independent slots start together.                                        │
│ If B depends on A's result, B belongs to the next wave.                      │
│                                                                              │
│ Slot input:                                                                  │
│   run_id + phase_id + wave_id + spec_revision + correlation_id + slot_id     │
│   attempt_id + one hypothesis + bounded source + expected fact + stop        │
│   depends_on_slot_ids=[] (proof of same-wave independence)                   │
│                                                                              │
│ Slot work:                                                                   │
│   collect bounded evidence                                                   │
│   [SLOT-WRITE] wave-<n>/slots/<slot-id>/attempts/<attempt-id>/report.md      │
│   ~~~> SlotReceipt {parent ids, attempt_id, status, report_ref, sha256, model}│
│                                                                              │
│ Slot status:                                                                 │
│   COMPLETE | NOT_APPLICABLE | UNAVAILABLE | FAILED                           │
│                                                                              │
│ Slot prohibitions:                                                           │
│   ╳ does not write shared state/spec/ledger/root/decision                    │
│   ╳ does not create a diagnosis                                              │
│   ╳ does not start a sibling or the next wave                                │
│   ╳ does not decide whether evidence is sufficient                           │
│                                                                              │
│ Transport outcome is created by Orchestrator without semantic reading:       │
│   RETURNED | FAILED | TIMED_OUT | CANCELLED                                  │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ SlotReceipt[] + DispatchReceipt[]
                                v
┌──────────────────────────────────────────────────────────────────────────────┐
│ 5. JOIN → MERGER                                                             │
│                                                                              │
│ Merger checks receipts against the immutable WaveSpec revision:              │
│   - every planned logical slot appears exactly once (effective)              │
│   - attempt history stays on disk; join keeps one terminal receipt           │
│   - a late receipt with an inactive attempt_id is ignored                    │
│   - run/wave/spec revision match                                             │
│   - report path = slots/<slot-id>/attempts/<attempt-id>/report.md            │
│   - report hash matches                                                      │
│   - REQUIRED did not vanish without a terminal transport outcome             │
│                                                                              │
│ [invalid/missing receipt?]                                                   │
│   ├─ transport failure and attempt_id < max_slot_attempts                    │
│   │    ~~~> ControllerAction: REDISPATCH_SLOT (next attempt_id)              │
│   ├─ another falsifiable fact can replace it                                 │
│   │    ~~~> ControllerAction: PREFLIGHT after a new spec revision            │
│   └─ no substitute                                                           │
│        └─ HARD_BLOCKER proposal candidate                                    │
│                                                                              │
│ [complete join]                                                              │
│   [MERGER-WRITE] wave-<n>/join-receipt.yaml                                  │
│   [MERGER-WRITE] evidence-ledger/<revision>.yaml                             │
│   [MERGER-WRITE] root-graph/<revision>.yaml                                  │
│   [MERGER-WRITE] wave-<n>/merge.md                                           │
│                                                                              │
│ Merger creates a Proposal, not a decision:                                   │
│   proposal_id + candidate_action                                             │
│   candidate_action = NEXT_WAVE_SPEC | END | HARD_BLOCKER                     │
│                                                                              │
│ [MERGER-WRITE] wave-<n>/proposals/<proposal_id>.yaml                         │
│ ~~~> ControllerAction: CALL_ADVOCATE                                         │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ Proposal
                                v
┌──────────────────────────────────────────────────────────────────────────────┐
│ 6. ADVOCATE GATE — READONLY CHALLENGE                                        │
│                                                                              │
│ Orchestrator ───> Advocate {proposal_id, root, evidence refs, candidate}     │
│ Advocate ~~~> AdvocatePacket {CLEAN | HOLE, one check if HOLE}               │
│ Orchestrator ───> Merger AdvocatePacket                                      │
│ [MERGER-WRITE] wave-<n>/advocate/<proposal_id>.yaml                          │
│                                                                              │
│ Advocate:                                                                    │
│   ╳ does not write a file                                                    │
│   ╳ does not create a decision/wave                                          │
│   ╳ does not change the root graph                                           │
│                                                                              │
│ [candidate × Advocate]                                                       │
│                                                                              │
│   END + CLEAN                 ──> accept END                                 │
│   END + HOLE material         ──> revised NEXT proposal                      │
│   END + HOLE immaterial       ──> accept END + recorded rationale            │
│                                                                              │
│   NEXT + CLEAN                ──> accept NEXT_WAVE_SPEC                      │
│   NEXT + HOLE                 ──> revised NEXT with a falsifiable check      │
│                                                                              │
│   HARD_BLOCKER + CLEAN/HOLE   ──> ControllerAction: BLOCKER_RECOVERY         │
│       one BLOCKER_RECOVERY_SPEC revision (≤1 REQUIRED slot) per proposal_id  │
│       then PREFLIGHT; forbidden at wave 20 / after checkpoint 20             │
│       cap HARD_BLOCKER → DELIVER only; no second recovery per proposal_id    │
│       ├─ capability unchanged ──> accept HARD_BLOCKER                        │
│       └─ material new fact    ──> new proposal_id + CALL_ADVOCATE            │
│                                                                              │
│ decision_id appears only here, after settlement.                             │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ accepted candidate
                                v
┌──────────────────────────────────────────────────────────────────────────────┐
│ 7. ACCEPTED DECISION + WAVE COUNTER                                          │
│                                                                              │
│ [MERGER-WRITE] decisions/<decision_id>.yaml                                  │
│ [MERGER-WRITE] events/<seq>-decision-accepted.yaml                           │
│ [MERGER-WRITE] state/current.yaml  (CAS: expected_state_revision)            │
│                                                                              │
│ POST_WAVE NEXT_WAVE_SPEC at wave 10/20 authorizes checkpoint evaluation,     │
│ not dispatch of wave N+1.                                                    │
│                                                                              │
│ [decision]                                                                   │
│                                                                              │
│   END                                                                        │
│     └─> L1_CONCLUDED ──> DELIVERY ──> optional L2 gate                       │
│                                                                              │
│   HARD_BLOCKER                                                               │
│     └─> L1_BLOCKED ──> DELIVERY                                              │
│                                                                              │
│   NEXT_WAVE_SPEC                                                             │
│     └─> inspect accepted wave number                                         │
│          ├─ wave 1..9                                                        │
│          │    ├─ ONE_WAVE   ──> PAUSED_AFTER_WAVE → DELIVER                  │
│          │    └─ CONTINUOUS ──> PREFLIGHT(next wave)                         │
│          │                                                                   │
│          ├─ wave 10 ──> ControllerAction: CALL_BOSS (checkpoint 10)          │
│          │                                                                   │
│          ├─ wave 11..19                                                      │
│          │    ├─ ONE_WAVE   ──> PAUSED_AFTER_WAVE → DELIVER                  │
│          │    └─ CONTINUOUS ──> PREFLIGHT(next wave)                         │
│          │                                                                   │
│          └─ wave 20 ──> ControllerAction: CALL_BOSS (final checkpoint 20)    │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ checkpoint only
                                v
┌──────────────────────────────────────────────────────────────────────────────┐
│ 8. BOSS CHECKPOINTS — AFTER WAVE 10 AND WAVE 20                              │
│                                                                              │
│ Boss is invoked only when the checkpoint has no accepted END/HARD_BLOCKER.   │
│                                                                              │
│ Merger forms a compact CheckpointPacket:                                     │
│   current root graph + accepted decision chain + contradictions              │
│   open gaps + attempted checks + evidence refs + remaining wave budget       │
│                                                                              │
│ Orchestrator ───> Boss CheckpointPacket                                      │
│ Boss ~~~> BossPacket:                                                        │
│   challenge + alternative roots + confidence basis                           │
│   duplicated/low-value paths + one highest-value next check                  │
│                                                                              │
│ Boss:                                                                        │
│   ╳ does not write files                                                     │
│   ╳ does not create NEXT/END/BLOCKER                                         │
│   ╳ does not start slots/Implementer                                         │
│                                                                              │
│ Orchestrator ───> Merger BossPacket                                          │
│ [MERGER-WRITE] checkpoints/<10|20>/boss.yaml                                 │
│                                                                              │
│ Merger re-synthesis uses:                                                    │
│   all prior accepted state + BossPacket + unresolved evidence gaps           │
│                                                                              │
│ [MERGER-WRITE] checkpoints/<10|20>/proposals/<proposal_id>.yaml              │
│ Orchestrator ───> Advocate ───> Merger                                       │
│                                                                              │
│ [checkpoint 10 result]                                                       │
│   ├─ END          ──> accepted decision → DELIVERY                           │
│   ├─ HARD_BLOCKER ──> accepted decision → DELIVERY                           │
│   └─ NEXT         ──> accepted decision → PREFLIGHT wave 11                  │
│                                                                              │
│ [checkpoint 20 result]                                                       │
│   ├─ END          ──> accepted decision → DELIVERY                           │
│   ├─ HARD_BLOCKER ──> accepted decision → DELIVERY + attention               │
│   └─ NEXT/HOLE/unresolved                                                    │
│       └─> wave 21 is forbidden                                               │
│           [MERGER-WRITE] state = WAITING_USER, pending_action=NONE,          │
│                           awaiting_input=USER, reason = WAVE_CAP             │
│           [MERGER-WRITE] lifecycle attention event                           │
│           └─> CHAT DELIVERY + mandatory Slack attention                      │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                v
┌──────────────────────────────────────────────────────────────────────────────┐
│ 9. DELIVERY + SLACK                                                          │
│                                                                              │
│ Merger forms the immutable summary/event:                                    │
│   [MERGER-WRITE] deliveries/<event_id>/chat-summary.md                       │
│   [MERGER-WRITE] deliveries/<event_id>/lifecycle.json                        │
│   ~~~> DeliveryPacket {parent ids, event_id, each exact path+sha256, type}   │
│                                                                              │
│ Orchestrator ───> user chat                                                  │
│                                                                              │
│ WAVE_CAP / unresolved after final checkpoint:                                │
│   notifier ───> Slack attention                                              │
│                                                                              │
│ Notifier reads the exact event ref/id from DeliveryPacket.                   │
│ ╳ does not search latest by mtime                                            │
│ ╳ does not change decision/state                                             │
│ ╳ does not start a wave                                                      │
│                                                                              │
│ Notification failure → delivery retry only.                                  │
│ ONE_WAVE pause → lifecycle kind=wave_result → Chat only, no Slack.           │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ accepted L1 END
                                v
┌──────────────────────────────────────────────────────────────────────────────┐
│ 10. IMPLEMENTER GATE                                                         │
│                                                                              │
│ [implementation_authorized in original/current user request?]                │
│                                                                              │
│   NO                                                                         │
│    └─> implementation_status = NOT_REQUESTED                                 │
│        L1 summary already delivered; Implementer is not called               │
│                                                                              │
│   YES                                                                        │
│    └─> Merger prepares a bounded ImplementationRequest                       │
│        [MERGER-WRITE] implementation/<phase_id>/request.yaml                 │
│        Orchestrator ───> Implementer                                         │
│                                                                              │
│        Implementer:                                                          │
│          [IMPL-WRITE] approved product changes                               │
│          runs relevant diff/build/tests                                      │
│          [IMPL-WRITE] implementation/<phase_id>/implementer-report.md         │
│          ~~~> ImplementationReceipt                                          │
│                                                                              │
│        Implementer:                                                          │
│          ╳ does not change L1 root/decision                                  │
│          ╳ does not broaden approved scope                                   │
│          ╳ does not declare product success                                  │
│          ╳ does not start investigation waves                                │
│                                                                              │
│        Orchestrator ───> Merger ImplementationReceipt                        │
│        Merger validates the receipt / requests independent validation slots  │
│                                                                              │
│        [validation result]                                                   │
│          ├─ VALIDATED                                                        │
│          │    └─> implementation=VALIDATED, product=MET                      │
│          │        [MERGER-WRITE] terminal LifecycleEvent + DeliveryPacket    │
│          │        ~~~> ControllerAction: DELIVER → user                      │
│          ├─ FAILED                                                           │
│          │    └─> implementation=FAILED, product=NOT_MET                     │
│          │        [MERGER-WRITE] terminal LifecycleEvent + DeliveryPacket    │
│          │        ~~~> ControllerAction: DELIVER → user                      │
│          └─ NEW_EVIDENCE                                                     │
│               └─> new phase_id linked by caused_by                           │
│                   original L1 decision remains immutable                     │
│                   [MERGER-WRITE] DeliveryPacket (new phase opened)           │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 4. State model

```text
investigation_status:
  BOOTSTRAP | ACTIVE | PAUSED_AFTER_WAVE | WAITING_USER | BLOCKED | CONCLUDED

implementation_status:
  NOT_REQUESTED | AUTHORIZED | IN_PROGRESS | VALIDATING | VALIDATED | FAILED

product_status:
  UNKNOWN | NOT_MET | MET

wave_budget:
  current_wave: 0..20
  boss_checkpoint_every: 10
  wave_cap: 20
  max_slot_attempts: <canonical configured value>
```

Examples:

- analysis-only L1 END: investigation `CONCLUDED`, implementation
  `NOT_REQUESTED`, product `UNKNOWN`
- original request included code changes and implementation succeeded:
  investigation `CONCLUDED`, implementation `VALIDATED`, product `MET`
- unresolved after final checkpoint: investigation `WAITING_USER`,
  `pending_action=NONE`, `awaiting_input=USER`, reason `WAVE_CAP`,
  `current_wave=20`

## 5. Ownership matrix

| Component | May invoke | May write | May decide |
|---|---|---|---|
| User | entry/resume/implementation authorization | nothing in run | intent and external choice |
| Orchestrator | Merger, Slot/Scout, Advocate, Boss, Implementer | nothing | nothing semantic |
| Slot/Scout | bounded evidence tools | own immutable report only | factual slot status only |
| Merger | no sibling dispatch; returns requested action | all shared run/wave artifacts | proposal, accepted transition after gates |
| Advocate | no agents | nothing | CLEAN/HOLE challenge only |
| Boss | no agents | nothing | checkpoint critique only |
| Implementer | approved product tools | approved product diff + own report | implementation receipt only |
| Stop-hook notifier | exact lifecycle event → Slack | external delivery/dedup state only | no run decision |

## 6. Scenario matrix

| Scenario | Required path | Forbidden shortcut |
|---|---|---|
| New run | Orchestrator → Merger bootstrap → preflight | Orchestrator-created manifest |
| Resume | `pending_action` + `awaiting_input` on current.yaml | latest file/mtime search |
| Stale preflight | Merger revised spec → preflight again | dispatch stale slots |
| Parallel wave | all independent slots in one batch | group-by-group serial dispatch |
| Slot timeout | DispatchReceipt → Merger REDISPATCH_SLOT / new spec revision / blocker | Orchestrator invents evidence |
| Normal wave result | join → proposal → Advocate → accepted decision | direct merge → next wave |
| Accepted NEXT at wave 10 | Boss → Merger re-synthesis → Advocate | direct wave 11 |
| Accepted NEXT at wave 20 | final Boss → Merger → Advocate → WAITING_USER | wave 21 |
| Unresolved after wave 20 | Chat summary + mandatory Slack attention | silent stop |
| L1 END, analysis-only request | deliver summary; no Implementer | automatic code edits |
| L1 END, original request authorized edits | automatic Implementer handoff | second permission request |
| Implementer says tests pass | Merger/validation evaluates receipt | self-declared product success |
| Implementation VALIDATED/FAILED | terminal DeliveryPacket to the user | silent L2 stop without delivery |
| New facts after implementation | new linked phase | rewrite prior accepted decision |

## 7. Non-negotiable invariants

```text
I01  Orchestrator writes zero files.
I02  Slot writes only its own immutable attempt report.
I03  Merger is the only writer of shared state and accepted decisions.
I04  Implementer writes code only when implementation_authorized=true.
I05  CODEX is absent from active routing.
I06  run_id equals the run folder name exactly.
I07  proposal_id and decision_id are different lifecycle identities.
I08  NEXT/END/HARD_BLOCKER exist only as accepted decisions after gates.
I09  Every wave join accounts for every planned logical slot exactly once
     (one effective terminal attempt).
I10  A dependent check cannot run in the same parallel wave as its prerequisite.
I11  Wave 11 requires checkpoint 10.
I12  Wave 21 is forbidden; wave cap is 20.
I13  Unresolved final checkpoint produces WAITING_USER + Slack attention.
I14  Boss and Advocate challenge; neither controls transitions.
I15  L1 END does not imply product MET.
I16  ImplementationReceipt does not imply VALIDATED.
I17  Accepted decisions are immutable; changed facts open a new phase/revision.
I18  Resume and notifier use exact IDs/pointers, never mtime.
I19  A passing fixture suite is insufficient; real run artifacts must validate.
I20  Historical/legacy runs cannot redefine current runtime contracts.
I21  Slot reports are write-once per (slot_id, attempt_id); join selects one
     effective terminal receipt per logical slot. Late attempts do not join.
I22  WaveSpec and preflight are write-once per revision_seq; REPLAN mints a
     new path. Singleton spec.yaml/preflight.yaml are not canonical.
I23  Orchestrator executes only a ControllerAction; it never infers the next
     role from decision prose.
I24  Merger updates current.yaml only when expected_state_revision matches
     current state_revision (CAS). Mismatch is STALE_TRANSITION, not a diagnosis.
I25  BLOCKER_RECOVERY is at most one BLOCKER_RECOVERY_SPEC per HARD_BLOCKER
     proposal_id. Forbidden at wave 20 / after checkpoint 20.
I26  POST_WAVE NEXT at wave 10/20 authorizes checkpoint evaluation, not
     dispatch of wave N+1. Wave 20 checkpoint NEXT cannot dispatch wave 21.
I27  After implementation VALIDATED/FAILED, Merger emits a terminal
     DeliveryPacket (product MET or NOT_MET).
I28  ControllerAction.action_id is the idempotency key. Orchestrator executes
     each id at most once. Resume reissues the same id until
     last_applied_action_id matches.
I29  pending_action is the next Orchestrator verb. After ASK_USER delivery,
     pending_action=NONE and awaiting_input=USER. Resume does not re-ask.
```

## 8. Canonical guarantees (validation surface)

These are required properties of the live loop, not a future checklist:

- Active agents, skills, commands, schemas, and the RUN template contain no
  CODEX route.
- Orchestrator is readonly and has no write paths.
- Slot / Merger / Advocate / Boss / Implementer ownership matches the matrix.
- All packet/state schemas exist with closed transition enums, including
  ControllerAction and CAS fields on CurrentState.
- Scenario tests cover checkpoint 10 and checkpoint 20, STALE_TRANSITION,
  attempt identity, revisioned spec paths, and L2 product MET/NOT_MET.
- Wave 21 cannot be dispatched.
- An unresolved checkpoint 20 yields `WAITING_USER/WAVE_CAP` and exact-id
  Slack attention.
- Analysis-only L1 does not call Implementer.
- A pre-authorized fix after accepted L1 END calls Implementer automatically.
- The runtime validator checks real new runs; their artifacts pass.
- No runtime reader selects authoritative state/delivery by mtime.

## 9. Blueprint / reference coverage

`BLUEPRINT-SCOUT` is an ordinary slot family inside the wave engine above, not
a separate orchestrator. Catalog registry:
`${CONTROL_PLANE_ROOT}/reference/blueprint-index.yaml`.

A catalog match is not a defect without local causal evidence. Qualification
(`eligible_zones`, `qualified_pairs`, `coverage_decision`) happens in Merger
after join, then independent pair checks run in a later wave.
