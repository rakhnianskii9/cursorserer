---
name: rkx-loop-bug
description: "Internal L1 symptom-investigation phase using the RKX wave protocol."
argument-hint: "${CONTROL_PLANE_ROOT}/runtime/logs/README.md <symptom> | <symptom>"
user-invocable: false
disable-model-invocation: true
---
# rkx-loop-bug

L1 only: collect and assess evidence; do not edit product code.

## Evidence protocol

Follow `rkx-loop-core`: bootstrap `merger` first returns a
`BOOTSTRAP_WAVE_SPEC` with evidence-backed hypotheses and narrow slots. Dispatch
its independent LOGS + CODE + DOCS slots in parallel; add DATA only for DB/API
scope. Groups are scope labels, not serial stages. After the fan-out join,
post-wave `merger` persists every slot report under
`loops/<run>/wave-N/slots/<slot-id>/report.md`, writes the wave artifacts, runs
the canonical Root-depth gate, and returns schema-v1 `NEXT_WAVE_SPEC`, `END`,
or `HARD_BLOCKER`. `HARD_BLOCKER` always enters the hard gate; otherwise select
the dual Advocate mode from root confidence:
- soft on locked success (`CLEAN` → Chat summary; `HOLE` → Chat summary + two-paragraph
  block, without auto-next);
- hard on `<96%` (CLEAN continues NEXT; HOLE → one next-check; HARD_BLOCKER →
  one `BLOCKER_RECOVERY`). Soft does not replace hard. Later waves target only
  recorded gaps and use the same fan-out.

Use direct targeted Read/search first. Use Tenets only for unknown scope after that; use CodeGraph/Octocode only for structural gaps; use logs, docs, and data only when relevant.

On stop / phase conclusion deliver **Chat summary ALWAYS** from `rkx-loop-core`
(5 parts in one English chat answer). Unconditional `N≥3` floor is not required;
slot count comes from `WAVE_SPEC`.
