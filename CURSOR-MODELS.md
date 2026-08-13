# Model routing policy

status: public template; runtime preflight required

No model API keys belong in this repository.

## Role bindings

| Role | Model |
|---|---|
| Orchestrator (`rkx-loop`) | `__MODEL_ORCHESTRATOR__` |
| Checkers (`fact-slot`, `cursor-fact-slot`) | `__MODEL_CHECKER__` |
| Blueprint Scout (`blueprint-scout`, `cursor-blueprint-scout`) | `__MODEL_CHECKER__` |
| Boss checkpoint (waves 10/20) | `__MODEL_BOSS__` |
| Advocate (`devil`) | `__MODEL_ADVOCATE__` |
| Merger | `__MODEL_MERGER__` |
| Implementer | `__MODEL_MERGER__` |

Before execution, verify that the current picker/catalog exposes the configured
variant. If unavailable, stop and ask the USER; never silently substitute a
model.

## Execution and billing routing

`token_mode` is an execution and billing/credential selection, not a model
selection:

| Token mode | Fact-slot role | Scout role | Billing/credential path |
|---|---|---|---|
| `API` | `fact-slot` | `blueprint-scout` | API credentials |
| `CURSOR` | `cursor-fact-slot` | `cursor-blueprint-scout` | Cursor subscription |

Active routes are `API | CURSOR` only. CODEX is not an active route. The two
modes may resolve to the same approved model binding. No artifact, prompt, or
policy file may contain credential values, account identifiers, or API keys.

## Delegation routing

- Checker slots use the preflight-verified checker binding (never an unverified
  `inherit` fallback) and are background fan-out roles: all independent slots
  in a wave are dispatched in parallel.
- `rkx-loop-orchestrator`, `merger`, `boss`, `devil`, `fact-slot`,
  `cursor-fact-slot`, `blueprint-scout`, `cursor-blueprint-scout`, and
  `implementer` are internal delegation roles, not slash commands. `boss` is
  checkpoint-only (waves 10/20) and never auto-spawns checker slots.
- Advocate (`devil`) runs once per Merger `proposal_id` and returns
  `AdvocatePacket` (`CLEAN`|`HOLE`) only. It does not write `loops/**`, decide
  transitions, or spawn slots. `decision_id` appears only after Merger
  settles the gate. Do not reuse `boss` for this gate.
- `merger` is the sole shared-state writer: bootstrap, preflight decision,
  join, proposals, accepted decisions, current state, and delivery packets.
  Orchestrator is readonly and executes only a `ControllerAction`.
- `implementer` is the writable L2 role. It is delegated when
  `implementation_authorized=true` (original request or later explicit gate)
  with Merger `ImplementationRequest`. It does not dispatch checker slots or
  override Merger/Boss.

## Binding doctrine

This file is the only approved role-binding policy. Agent frontmatter may
reference the exact policy-approved runtime alias required by Cursor. Other
rules, commands, and task prompts must not introduce ad-hoc model/version
pins. A policy binding is never proof of the model that executed a run; runtime
artifacts must record the selected model separately.

## Scope

This document defines Cursor routing only. Topology and ownership live in
`RKX-LOOP-BLUEPRINT-FLOW.md`.
