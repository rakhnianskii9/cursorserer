---
name: rkx-loop-design
description: "Internal design-decision phase for RKX work."
argument-hint: "<surface>"
user-invocable: false
disable-model-invocation: true
---
# rkx-loop-design

Record only the design decision needed to progress. This phase is L1 unless the user separately opens L2 implementation.

## Protocol

Use direct targeted Read/search first. Use Tenets only for unknown scope after that; use CodeGraph/Octocode only for structural gaps; use relevant design-system or UI evidence.

A wave (`rkx-loop-core`) starts only when the USER explicitly requests one. On
phase conclusion deliver **Chat summary ALWAYS** from `rkx-loop-core` (5 parts).
