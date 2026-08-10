# Model routing policy

status: public template; runtime preflight required

No model API keys belong in this repository.

## Role bindings

| Role | Model |
|---|---|
| Orchestrator (`rkx-loop`) | `<picker model id; verify during preflight>` |
| Checkers (`fact-slot`, `cursor-fact-slot`) | `<picker model id; verify during preflight>` |
| Blueprint Scout (`blueprint-scout`, `cursor-blueprint-scout`) | `<picker model id; verify during preflight>` |
| Manual Boss | `<picker model id; verify during preflight>` |
| Advocate (`devil`) | `<picker model id; verify during preflight>` |
| Merger | `<picker model id; verify during preflight>` |
| Implementer | `<picker model id; verify during preflight>` |

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

The two modes may resolve to the same approved model binding. No artifact,
prompt, or policy file may contain credential values, account identifiers, or
API keys.

## Delegation routing

- Checker slots use the preflight-verified checker binding (never an unverified
  `inherit` fallback) and are background fan-out roles: all independent slots
  in a wave are dispatched in parallel.
- `rkx-loop-orchestrator`, `merger`, `boss`, `devil`, `fact-slot`,
  `cursor-fact-slot`, `blueprint-scout`, `cursor-blueprint-scout`, and
  `implementer` are internal delegation roles, not slash commands. `boss` is
  manual-only and never auto-spawns checker slots.
- `Advocate (devil)` runs once per post-wave `decision_id` in **dual mode**:
  soft when `root >= 96%` (advisory; HOLE does not auto-continue), hard when
  `root < 96%` (former ALWAYS-ON gate; HOLE/BLOCKER_RECOVERY continue). Soft
  does not replace hard. `needs_devil` is legacy metadata only. It returns
  `ATTACK_PACKET` only; it does not write `loops/**`, decide any outcome, or
  spawn slots. Do not reuse `boss` for this gate.
- `merger` is the bootstrap planner before Wave 1 and the single fan-in,
  synthesis, Root-depth, and next-wave planner after every completed wave. It
  is not dispatched once per checker slot. Orchestrator picks soft/hard from
  root confidence before Advocate.
- `implementer` is the writable L2 role. It is delegated only after the
  explicit user gate and an approved implementation scope/plan with relevant
  Merger scenario/state/root evidence. It does not dispatch checker slots or
  override Merger/Boss/Devil.

## Binding doctrine

This file is the only approved role-binding policy. Agent frontmatter may
reference the exact policy-approved runtime alias required by Cursor. Other
rules, commands, and task prompts must not introduce ad-hoc model/version
pins. A policy binding is never proof of the model that executed a run; runtime
artifacts must record the selected model separately.

## Scope

This document defines Cursor routing only.
