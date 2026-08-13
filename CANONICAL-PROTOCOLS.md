# Canonical public protocols

This document is the public contract. The JSON Schemas under `schemas/` and
`schemas/packets/` are the machine-readable source of truth; examples and
validators must not invent a second field name for the same decision.
Topology and ownership live in `RKX-LOOP-BLUEPRINT-FLOW.md`.

## WAVE_SPEC v1

- `kind` is the spec envelope:
  `BOOTSTRAP_WAVE_SPEC`, `NEXT_WAVE_SPEC`, or `WAVE_DECISION`.
- Controlling **decisions** after gates are only
  `NEXT_WAVE_SPEC`, `END`, or `HARD_BLOCKER`.
- `proposal_id` exists before Advocate; `decision_id` appears only after
  accepted settlement.
- Runtime handoff is a closed `ControllerAction.action`, never inferred from
  decision prose.
- `decision_kind`, `candidate-END`, and parallel terminal fields are not
  canonical.
- `dispatch.mode` is `PARALLEL` and `dispatch.join` is `MERGER`.
- A slot receives exactly one supplied candidate hypothesis, one source, one
  expected fact, and one expected decision change.
- A fact-slot checks the supplied hypothesis. It does not create, rewrite, or
  reject hypotheses.
- Every confidence value is an exact `0%`–`100%` string with a non-empty
  `confidence_basis`.
- Active executor modes are `API | CURSOR` only.

## Lifecycle artifact v1

Every lifecycle artifact carries `schema_version`, `conversation_id`,
`event_id`, `run_id`, `phase_id`, `wave_id`, `kind`, `notification_type`,
`waiting_reason`, `correlation_id`, `problem_title`, and `summary`.

`kind` is one of `wave_result`, `waiting_user`, `blocked`, `completed`,
`failed`, or `wave_cap` (hooks may still accept `started`/`progress` as
non-Slack audit kinds). `notification_type` is either `attention` or
`result`. An artifact with `full_verdict_available: false` must not contain
`full_verdict_url`; an available URL must be an HTTP(S) URL without credentials.

Canonical delivery path is `loops/<run>/deliveries/<event_id>/lifecycle.json`
selected by exact event id from `state/current.yaml`. The notifier does not
pick artifacts by mtime. Slack is optional and disabled until installation
preflight confirms it.

## Interactive phases

- A wave starts only after an explicit user request.
- A short plan, design, front, or validation command may complete without a
  wave verdict.
- A question phase such as `/loop-grill-me` asks its question and waits. It
  does not emit the terminal five-part summary.
- The full Chat summary is emitted only at terminal completion, a ONE_WAVE
  pause (`wave_result`), or an explicitly confirmed terminal recovery.
  Merger writes `deliveries/<event_id>/chat-summary.md`; Orchestrator delivers
  the DeliveryPacket and writes no files.

## Capability and model policy

The installation preflight verifies models, MCP servers, browser access, logs,
and Canvas declarations. A role binding is policy metadata, not evidence that a
runtime model executed the run. Unavailable optional capabilities are recorded
as unavailable or skipped and do not become fake active requirements.

See:

- `RKX-LOOP-BLUEPRINT-FLOW.md`
- `schemas/wave-spec-v1.json`
- `schemas/lifecycle-artifact-v1.json`
- `schemas/packets/`
- `schemas/runtime-inputs-v1.json`
- `INSTALL-WITH-CURSOR.md`
