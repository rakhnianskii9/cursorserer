---
name: rkx-loop-implement
description: "Internal L2 implementation phase with RKX safety gates."
argument-hint: "after L2 gate"
user-invocable: false
disable-model-invocation: true
---
# rkx-loop-implement

Proceed only when `implementation_authorized=true` (original request or a later
explicit L2 gate such as `Smash`) and Merger has written
`ImplementationRequest`. The readonly orchestrator delegates this work to
`implementer` with that request plus the approved scope/plan and relevant
Merger scenario, state, and root-cause evidence. The implementer follows that
scope, creates the nginx pre-copy before nginx edits, avoids secrets and
destructive Git, and returns `ImplementationReceipt` plus the resulting diff
to validation. Receipt is not product success.

## Implementer boundaries

- Implement only the approved scope; do not broaden it, invent a diagnosis, or
  override Merger/Boss.
- Do not dispatch wave checkers or initiate a wave investigation. Missing
  evidence is returned to the caller for routing.
- Report changed files and relevant validation results.
- After L2 leaf / handoff to validate, the caller delivers **Chat summary ALWAYS**
  from `rkx-loop-core` (5 parts). Implementer itself returns changed files and
  validation evidence; it does not replace the orchestrator chat report.

`Build` is not Docker authorization; Docker additionally requires green `Build`
validation and `Ship` or `Build docker`.
