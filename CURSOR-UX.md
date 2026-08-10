# Cursor UX — RKX Loops (production)

## Mode dropdown (Agent / Plan / Ask / Debug)

**Cannot** add `RKX-Loop` there. Custom Modes were removed in Cursor 2.1. SoT: ADR-012.

Work in **Agent**, then use slash commands.

## How to launch (canonical)

1. **Reload Window** (once after `.cursor/commands/` appears).
2. Chat → mode **Agent**.
3. Type `/` in the input → these should appear:
   - `/rkx-loop` — start a wave investigation
   - `/loop-bug` — shortcut for investigating a symptom
   - `/loop-validate` — targeted plan/diff validation
   - `/loop-boss` — manual adversarial check of wave state
4. Delegation: the primary agent selects an internal role from
   `.cursor/agents/`; this is not a slash interface.

`rkx-loop-core` and phase skills are internal implementation details, not
commands for manual selection.

`/rkx-loop` belongs only to `.cursor/commands/`. The
`rkx-loop-orchestrator` agent (file `.cursor/agents/rkx-loop.md`) is an
internal delegated role and is never invoked as a slash command.

## Internal delegation roles

These headers are visible in the agent picker, but none creates an additional
slash command:

| Role | When to choose | Header behavior |
|---|---|---|
| `rkx-loop-orchestrator` | coordinate an explicit wave | the verified orchestrator model |
| `fact-slot` | evidence slot | the verified checker model, read-only, background |
| `cursor-fact-slot` | evidence slot (Cursor alias) | the verified checker model, read-only, background |
| `blueprint-scout` | reference-pattern discovery slot | the verified checker model, read-only, background |
| `cursor-blueprint-scout` | reference-pattern discovery slot (Cursor alias) | the verified checker model, read-only, background |
| `merger` | plans the wave at bootstrap; after join, saves slot reports, writes merge/state/status/root graph/ledger, and plans the next wave | the verified Merger model, writable only for loop artifacts |
| `devil` / Advocate | dual-mode: soft ≥96% (advisory) / hard <96% (gate) → `ATTACK_PACKET` | the verified Advocate model (`__MODEL_ADVOCATE__`), read-only; does not write `loops/**` or decide END/NEXT/HARD_BLOCKER |
| `boss` | manual bounded check | the verified Boss model, read-only |
| `implementer` | L2 changes after an explicit USER gate | the verified Merger model, writable; approved scope/plan + Merger evidence only |

The three-stage command pipeline is:

- `Smash` — implement or make changes.
- `Build` — build and validate.
- `Ship` — release or deploy.

`implementer` is selected for delegation only after the literal user gates
`Smash`; its header does not create a slash command. The orchestrator invokes
one mode-specific fact slot (`fact-slot` or `cursor-fact-slot`) for preflight and saves only the matching
`loops/<run>/wave-N/preflight.yaml`; `merger` saves the
remaining loop artifacts for each wave under `loops/<run>/**`. Only
`implementer` performs L2 product changes; Docker still requires a separate
Ship gate.

## Parallel wave dispatch

Before the first wave, bootstrap-Merger is invoked. It forms
`BOOTSTRAP_WAVE_SPEC`: hypotheses, slots, expected facts, and the stop contract.
The orchestrator does not invent its own hypotheses; it only executes the spec.

Independent checker slots in a wave are launched **in parallel in one
fan-out batch**. LOGS, CODE, DOCS, applicable DATA, and `BLUEPRINT-SCOUT` are
scope groups, not a stage queue: do not wait for one slot/group to finish
before launching the next. The checker runs in the background and does not
write a shared artifact. `REFERENCE-COVERAGE` runs later only for
Merger-qualified `zone × reference entry` pairs, not for the full catalog
Cartesian product.

After every slot has returned a result or an explicit terminal failure has been
recorded for it, one fan-in/join runs through `merger`. Merger first saves each
result to `loops/<run>/wave-N/slots/<slot-id>/report.md`, then runs the
Root-depth gate and a separate synthesis check, and returns schema-v1
`NEXT_WAVE_SPEC`, `END`, or `HARD_BLOCKER`. The next wave depends on this merge, but its
independent slots are again launched in parallel. If the runtime limits the
number of concurrent agents, bounded concurrent batches marked `DEGRADED` are
allowed; intentionally launching one at a time is forbidden.

### Preflight before dispatch

Before each fan-out, the Orchestrator invokes and awaits one mode-specific
checker (`fact-slot` for API or `cursor-fact-slot` for CURSOR) in the `PREFLIGHT` group. The selected checker
collects source/tool/MCP/browser
capability, authenticated context, read-only scope, safe `correlation_refs`, and
the code/catalog/config revision. The Orchestrator verifies `spec_revision` and
writes the write-once `preflight.yaml`; Merger does not participate.
`STALE_SCOPE` returns the spec to Merger, while `WAITING_USER` / `BLOCKED`
require the single USER choice: **check as-is**, **provide what's needed**, or
**stop**.

### DUAL ADVOCATE GATE (soft ≥96% / hard <96%)

After post-wave Merger, any `HARD_BLOCKER` enters the hard gate before
confidence is evaluated. Otherwise the orchestrator checks `root confidence`.

- **SOFT** (`root >= 96%` + Root-depth PASS): success is locked; one
  advisory audit by `Advocate (devil)`. Soft does not cancel success or start a
  wave/recovery. `CLEAN` → Chat summary. `HOLE` → Chat summary + a
  `### HOLE — identified gap` block (max 2 paragraphs); follow-up only on a
  USER command.
- **HARD** (`root < 96%`, incomplete Root-depth, or `HARD_BLOCKER`): Advocate before dispatch/accept/stop (the former
  ALWAYS-ON gate). `CLEAN` + NEXT → parallel fan-out; `HOLE` → one
  `SINGLE_NEXT_CHECK`; `HARD_BLOCKER` → one `BLOCKER_RECOVERY`. Soft does not
  replace hard.
- A Merger⇄Devil chat loop and a second Advocate for the same `decision_id` are
  forbidden.
- `boss` / `/loop-boss` do not participate in this gate.

Merger's canonical Root-depth questions:

1. Is this the final logical status of the answer?
2. Does it explain the deep root cause (not a label or symptom)?
3. Do we need to dig deeper?
4. What next question would expose another layer (down to API/runtime/language
   semantics if needed)?

In every slot/source/hypothesis/root/decision artifact, confidence is stored
only as a `0%`–`100%` percentage. The formats `high`, `medium`, `0.92`,
`approximately`, and `NOT_STATED` are forbidden; alongside it, preserve
`CONFIDENCE_BASIS`.

## Chat summary ALWAYS

After soft END (`CLEAN`/`HOLE`) / confirmed recovery `HARD_BLOCKER` / phase
completion, the orchestrator **must** deliver a complete five-part Chat summary in
English: a business/UI sentence, a five-column table, technical facts, an
ASCII/box-drawing diagram, and a human-readable `### 5) Verdict` ✅/❌.
Part 5 follows the binding template in
`.cursor/skills/rkx-loop-core/SKILL.md`: an arbitrary-length causal chain,
translation of facts into UI/business logic, and `**Basis:** *...*` /
`**Where:** *evidence-id · exact % · factual model*`. Role binding must be
explicitly marked and must not be presented as the model that ran. Files under
`loops/<run>/` are evidence, not a substitute for chat.
Molecule 2 = Verdict; molecule 12 = ASCII. Without all five parts, the result
is considered undelivered.

## Slack notify (phone)

Cursor Slack Cloud Agents ≠ a local Agent Chat notification. For a local loop:

- stop-hook `.cursor/hooks/rkx-slack-notify.sh` sends only two run-scoped cards
  from `loops/<run>/slack-notification.json`: `attention` when USER input or a
  decision is required, and `result` when the loop completes;
- after a Chat summary has actually been delivered, MCP may send a separate full
  verdict; the hook does not rebuild it from `state.md`;
- the card contains a detailed problem title, user-facing meaning, an optional
  blocker, one next action, and `run · wave`;
- when there is no exact artifact/conversation match or Slack transport fails,
  the hook stays silent and does not break Cursor; `conversation_id` cannot be a
  placeholder;
- real `Continue checking` / `Stop` actions are not shown until callback/backend
  paths exist; a working link to the full result is allowed.

Canonical schema and ownership: `.cursor/skills/rkx-loop-core/SKILL.md`.
Secrets belong only in `~/.cursor/rkx-slack-notify.env`. Push to a phone = a
Slack app.

## SoT files

| What | Path |
|---|---|
| Slash commands | `.cursor/commands/*.md` |
| Skills | `.cursor/skills/rkx-loop-*/SKILL.md` |
| Delegation agents | `.cursor/agents/*.md` |
| Rules | `.cursor/rules/rkx-*.mdc` (+ `token-economy`, `normal-agent-workflow`, …) |
| Models | `.cursor/CURSOR-MODELS.md` |
| Reference catalogs | `.cursor/reference/blueprint-index.yaml`, `.cursor/reference/system-design-primer/`, `.cursor/reference/telephony/catalog.yaml` |
| Gate / optional runs | `.cursor/rules/infrastructure-core.mdc` + `rkx-always-on.mdc`, `loops/` |

Wave protocol starts only from `/rkx-loop` and `/loop-bug` (see `rkx-always-on.mdc`). Other `/loop-*` are focused phase helpers unless USER asks for a wave.

User mirror commands: `~/.cursor/commands/` (the same set).

## Not SoT for Cursor slash

- `.cursor/prompts/` — legacy prompt-file layout (a mirror may be kept, but
  Cursor's `/` menu reads **commands** + **skills**).
