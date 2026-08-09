---
name: rkx-loop-plan
description: "Internal L1 planning phase for RKX work."
argument-hint: "from findings"
user-invocable: false
disable-model-invocation: true
---
# rkx-loop-plan

Create a concise, evidence-backed implementation plan. L1 forbids product edits. Include only relevant scope, safety constraints, validation, and rollback notes.

## Protocol

Use direct targeted Read/search first. Use Tenets only for unknown scope after that; use CodeGraph/Octocode only for structural gaps; use logs, docs, and data only when relevant.

A wave (`rkx-loop-core`) starts only when the USER explicitly requests one,
including `/rkx-loop` or `/loop-bug`. Material uncertainty alone requires
focused clarification or a direct planning note; it never starts a wave. On a
resolved phase conclusion, deliver **Chat summary ALWAYS** from
`rkx-loop-core` (5 parts).
