---
description: RKX L1 wave investigation for a reported symptom
argument-hint: "${CONTROL_PLANE_ROOT}/runtime/logs/README.md <symptom>"
---
# /loop-bug

Load `rkx-loop-core` and `rkx-loop-bug`. This is L1: collect and assess
evidence only; no product edit without a later explicit L2 request.

Ask for token mode (**API** or **Cursor**), then delegate `merger` in bootstrap
mode. Wait for its `BOOTSTRAP_WAVE_SPEC`; it defines the hypotheses, slots,
expected facts, and output directory. Do not create a competing hypothesis in
the command. Dispatch the spec's independent LOGS + CODE + DOCS slots as one
parallel batch; add DATA only for DB/API scope. When the bootstrap spec
contains `BLUEPRINT-SCOUT`, dispatch `blueprint-scout` in API mode or
`cursor-blueprint-scout` in Cursor mode using its explicit `CATALOG_ID`; it
reads only the normalized local registry, selected catalog index and exact
pinned local source refs.

Preserve the original reported symptom as the run's `problem_title` and bind
the lifecycle notification artifact to the current `conversation_id`. The
artifact may produce only an `attention` or `result` Slack card; `started` and
`progress` are audit-only. It must never replace the five-part Chat summary or
infer a root from `state.md`.

Groups are not sequential stages. Slots must each have one hypothesis/source
and one expected fact. Checkers verify evidence only and run in the
background. After all slots return or fail explicitly, delegate one post-wave
merger. It stores each report under
`loops/<run>/wave-N/slots/<slot-id>/report.md`, runs the Root-depth gate, and
returns schema-v1 `NEXT_WAVE_SPEC`, `END`, or `HARD_BLOCKER`. A
`HARD_BLOCKER` always enters the hard gate; otherwise choose Advocate mode from
root confidence and Root-depth:
- `root >= 96%` → **SOFT**: success locked; one advisory Advocate. `CLEAN` →
  Chat summary. `HOLE` → Chat summary + optional `### HOLE` (max 2 paragraphs); no
  auto-next; follow-up only on USER command.
- `root < 96%` → **HARD**: Advocate before dispatch/accept/stop. `CLEAN`
  continues NEXT; `HOLE` → one falsifiable next-check or re-synthesis;
  `HARD_BLOCKER` → one `BLOCKER_RECOVERY` (`boss` not in this gate). Soft does
  not replace hard.

Subsequent waves must target recorded gaps and use the same parallel fan-out.
Stop at soft END with `>= 96%`, or a confirmed hard recovery blocker.

On stop, deliver **Chat summary ALWAYS** (all 5 parts in one English chat answer):
business/UI sentence, five-column table, tech facts with conf%, ASCII schema,
human ✅/❌ Verdict. Part 5 must follow the binding template in
`${CONTROL_PLANE_ROOT}/skills/rkx-loop-core/SKILL.md`: arbitrary-length causal chain,
business/UI translation, `**Basis:** *...*`, and
`**Where:** *evidence-id · exact % · factual model*` for every link. Role
binding must be disclosed and never presented as the model that ran.
`loops/<run>/` is evidence SoT, not a chat substitute. Do not end with
path-only / harness-only status.

After the complete Chat summary, MCP may send one separate full verdict to Slack.
The stop hook remains the fail-open lifecycle fallback; it must not send a
duplicate full verdict or expose raw slot output.
