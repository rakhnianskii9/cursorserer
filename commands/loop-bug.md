---
description: RKX L1 wave investigation for a reported symptom
argument-hint: "@<log-source> <symptom>"
---
# /loop-bug

Load `rkx-loop-core` and `rkx-loop-bug`. This is L1: collect and assess
evidence only; no product edit without a later explicit L2 request.

Use the caller-recorded token mode (**API** or **CURSOR**) and
matching billing scope, then delegate `merger` in bootstrap mode. Wait for its `BOOTSTRAP_WAVE_SPEC`; it defines the hypotheses, slots,
expected facts, and output directory. Do not create a competing hypothesis in
the command. Dispatch the spec's independent LOGS + CODE + DOCS slots as one
parallel batch; add DATA only for DB/API scope. When the bootstrap spec
contains `BLUEPRINT-SCOUT`, dispatch `blueprint-scout` for API,
`cursor-blueprint-scout` for CURSOR using
its explicit `CATALOG_ID`; it
reads only the normalized local registry, selected catalog index and exact
pinned local source refs.

Preserve the original reported symptom as the run's `problem_title` **and**
record `success_criteria` + `goal_closure` per `rkx-loop-core` (grill once if
PASS ambiguous; soft END only when product goal met or explicit title-only
scope). Bind the lifecycle notification artifact to the current
`conversation_id`. The artifact may produce only an `attention` or `result`
Slack card; `started` and `progress` are audit-only. It must never replace the
five-part Chat summary or infer a root from `state/current.yaml`. Chat part 1 and Verdict
must quote `success_criteria`.

Groups are not sequential stages. Slots must each have one hypothesis/source
and one expected fact. Max **10 slots per wave**. Checkers verify evidence only
and run in the background. After all slots return or fail explicitly, delegate
one post-wave merger. Checkers write
`loops/<run>/wave-<n>/slots/<slot-id>/attempts/<attempt-id>/report.md`. Merger
emits a Proposal; Orchestrator calls Advocate once per `proposal_id`; accepted
actions are `NEXT_WAVE_SPEC`, `END`, or `HARD_BLOCKER`. POST_WAVE NEXT at wave
10/20 is a Boss checkpoint, not dispatch of N+1.

Subsequent waves must target recorded gaps and use the same parallel fan-out.
Stop at accepted END with `>= 96%` **and** `product_goal_met` (or disclosed
`title_only_scope`), or a confirmed HARD_BLOCKER after at most one recovery.

On stop, deliver **Chat summary ALWAYS** (all 5 parts in one English chat answer):
business/UI sentence **quoting `success_criteria`**, five-column table, tech facts
with conf%, ASCII schema, human ✅/❌ Verdict that also quotes `success_criteria`
and states `goal_closure`. Part 5 must follow the binding template in
`.cursor/skills/rkx-loop-core/SKILL.md`: arbitrary-length causal chain,
business/UI translation, `**Basis:** *...*`, and
`**Where:** *evidence-id · exact % · factual model*` for every link. Role
binding must be disclosed and never presented as the model that ran.
`loops/<run>/` is evidence SoT, not a chat substitute. Missing
`success_criteria` cites → `chat_itog_delivered` FAIL. Do not end with
path-only / harness-only status.

After the complete Chat summary, MCP may send one separate full verdict to Slack.
The stop hook remains the fail-open lifecycle fallback; it must not send a
duplicate full verdict or expose raw slot output.
