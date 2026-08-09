# Canonical public protocols

This document is the public contract. The JSON Schemas under `schemas/` are
the machine-readable source of truth; examples and validators must not invent a
second field name for the same decision.

## WAVE_SPEC v1

- `kind` is the spec envelope:
  `BOOTSTRAP_WAVE_SPEC`, `NEXT_WAVE_SPEC`, or `WAVE_DECISION`.
- `decision` is the terminal/continuation enum:
  `NEXT_WAVE_SPEC`, `END`, `HARD_BLOCKER`, `BLOCKER_RECOVERY`, or
  `SINGLE_NEXT_CHECK`; it is `null` during bootstrap.
- `decision_kind`, `candidate-END`, and parallel terminal fields are not
  canonical.
- `dispatch.mode` is `PARALLEL` and `dispatch.join` is `MERGER`.
- A slot receives exactly one supplied candidate hypothesis, one source, one
  expected fact, and one expected decision change.
- A fact-slot checks the supplied hypothesis. It does not create, rewrite, or
  reject hypotheses.
- Every confidence value is an exact `0%`–`100%` string with a non-empty
  `confidence_basis`.

## Lifecycle artifact v1

Every lifecycle artifact carries `schema_version`, `conversation_id`,
`event_id`, `run_id`, `wave`, `kind`, `notification_type`, `problem_title`,
`summary`, and `full_verdict_available`.

`kind` is one of `started`, `progress`, `waiting_user`, `blocked`, `completed`,
`failed`, or `wave_cap`. `notification_type` is either `attention` or
`result`. An artifact with `full_verdict_available: false` must not contain
`full_verdict_url`; an available URL must be an HTTP(S) URL without credentials.

The local stop hook sends only the run-scoped attention/result card. It does not
reconstruct a verdict from a global state file. Slack is optional and disabled
until installation preflight confirms it.

## Interactive phases

- A wave starts only after an explicit user request.
- A short plan, design, front, or validation command may complete without a
  wave verdict.
- A question phase such as `/loop-grill-me` asks its question and waits. It
  does not emit the terminal five-part summary.
- The full Chat summary is emitted only at terminal completion or an explicitly
  confirmed terminal recovery.

## Capability and model policy

The installation preflight verifies models, MCP servers, browser access, logs,
and Canvas declarations. A role binding is policy metadata, not evidence that a
runtime model executed the run. Unavailable optional capabilities are recorded
as unavailable or skipped and do not become fake active requirements.

See:

- `schemas/wave-spec-v1.json`
- `schemas/lifecycle-artifact-v1.json`
- `schemas/runtime-inputs-v1.json`
- `INSTALL-WITH-CURSOR.md`
