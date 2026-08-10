---
description: Start an explicit RKX wave investigation.
argument-hint: <scenario or symptom>
---

# /rkx-loop

Run the explicit wave protocol in `rkx-loop-core`. The caller records one supported
token mode: `CURSOR` for the Cursor subscription, or `API` only when API credentials are explicitly available.
Record matching scope (`API_CREDENTIALS` or `CURSOR_SUBSCRIPTION`); never invent a mode or credential.
Then delegate the bootstrap planner `merger` and wait
for its `BOOTSTRAP_WAVE_SPEC`. Do not invent slots in the command or
orchestrator. The spec normally covers **LOGS + CODE + DOCS**; include
**DATA** only for a database or external API scope.

At bootstrap, preserve the user's original scenario as `problem_title` **and**
record `success_criteria` (PASS in USER/business language) with
`source: user_explicit | user_inferred_confirmed | title_only_scope`. If PASS
is ambiguous vs a title keyword, ask exactly one grill question before
`BOOTSTRAP_WAVE_SPEC` fan-out (lifecycle `waiting_user`) or get explicit
`title_only_scope`. Soft `END` requires `product_goal_met` (or disclosed
title-only scope). Evidence-first: runtime/capture failure modes lead over
title-keyword side-quests unless title-only. Bind the exact current
`conversation_id` (never a placeholder). Each meaningful lifecycle transition
writes the run-scoped `loops/<run>/slack-notification.json` artifact. Slack
sends only two card types: `attention` when USER input/decision is required
and `result` when the loop is complete. The cards are short and human-readable;
they are not substitutes for the full five-part Chat summary.

Before every fan-out, the orchestrator invokes and awaits one mode-specific
checker with group `PREFLIGHT`: `fact-slot` for API, `cursor-fact-slot` for
observations for every planned slot; the orchestrator verifies the exact
`spec_revision` and writes `preflight.yaml` with `orchestrator_resolution`.
Validate `CAPABILITY_PREFLIGHT` against that revision before dispatch; every
planned slot must declare `expected_decision_change`. Merger does not participate. `STALE_SCOPE` returns the spec to Merger; a
non-ready `REQUIRED` slot requires the single USER choice: **check as-is**,
**provide what's needed**, or **stop**. A non-ready `OPTIONAL` slot is
recorded as skipped/degraded and does not block READY slots.

For checkers, route by token mode: API → `fact-slot`, CURSOR → `cursor-fact-slot`. Verify the policy-approved
model in the active picker/catalog before launch; never silently substitute.

For the `BLUEPRINT-SCOUT` group, route API → `blueprint-scout`, CURSOR → `cursor-blueprint-scout`. Scout receives an explicit
`CATALOG_ID`, reads only the local registry, selected catalog index and exact
pinned local source refs supplied by its slot. It returns candidate reference
entries only; it does not decide coverage or root cause. Mixed generic and
telephony scope uses separate bounded Scout slots.

Keep every slot narrow: one hypothesis or source and one expected fact. Use
1–10 slots per group. Dispatch independent slots concurrently in one batch.
After the fan-out join, delegate one post-wave merger; it saves each packet
under `loops/<run>/wave-N/slots/<slot-id>/report.md`, runs the Root-depth gate,
and returns a schema-v1 `NEXT_WAVE_SPEC`, `END`, or `HARD_BLOCKER`.
`HARD_BLOCKER` always selects **HARD** before confidence is evaluated; otherwise
choose Advocate mode from root confidence and Root-depth:
- Soft candidate only when `root >= 96%`, Root-depth PASS, **and**
  `product_goal_met` (or disclosed `title_only_scope`): one advisory Advocate.
  `CLEAN` → Chat summary. `HOLE` → Chat summary + optional `### HOLE` block
  (max 2 paragraphs); no auto-next wave; follow-up only on USER command.
- Otherwise **HARD**: one Advocate gate before dispatch/accept/stop.
  `CLEAN` continues `NEXT_WAVE_SPEC`; `HOLE` uses one falsifiable next-check
  that advances `success_criteria` (no title-keyword reframe) or re-synthesis;
  `HARD_BLOCKER` gets one `BLOCKER_RECOVERY` handoff
  (`recovery_attempted: true` or one-check NEXT). Soft does not replace hard.
  Do not use `boss`, repeat Devil for the same decision, or spin on unavailable
  access.

On stop / phase conclusion, deliver **Chat summary ALWAYS** (5 parts in one
English chat answer): business/UI sentence **quoting `success_criteria`**,
five-column table, tech facts, ASCII schema, human ✅/❌ Verdict that also
quotes `success_criteria` and states `goal_closure`. Part 5 must follow the
binding template in `.cursor/skills/rkx-loop-core/SKILL.md`: arbitrary-length
causal chain, business/UI translation, `**Basis:** *...*`, and
`**Where:** *evidence-id · exact % · factual model*` for every link. Role
binding must be disclosed and never presented as the model that ran. Run files
are not a chat substitute. Molecules 2 and 12 bind Part 5 and the ASCII
schema. Missing `success_criteria` cite in part 1 or Verdict =
`chat_itog_delivered` FAIL. See `rkx-loop-core`.

After a complete Chat summary, MCP may send one separate full verdict to Slack.
The stop hook sends only the run-scoped lifecycle card and must not rebuild a
verdict from `state.md`. Missing notification artifacts fail open and do not
block Cursor.

Start ordinary, non-loop code requests directly; do not invoke this command for
routine implementation.

## Safety

Apply the explicit L1/L2, nginx, Docker, secrets, browser, and destructive-git
guards from `infrastructure-core.mdc` / `rkx-always-on.mdc` and workspace rules. Finish with Chat summary, not a
path-only handoff.

## Skills

`rkx-loop-core`, phase `rkx-loop-*`, KEEP: `rkx-tenets`, `graph-octocode`, `rkx-codegraph`, `octocode-code-forensics`, `rkx-mcp-utilities`, `meta-developer-tools`, `browser-ui-evidence`, `docker-diagnostics`.
