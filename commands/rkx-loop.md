---
description: Start an explicit RKX wave investigation.
argument-hint: <scenario or symptom>
---

# /rkx-loop

Run the explicit wave protocol in `rkx-loop-core`. First ask for token mode:
**API** or **Cursor**. Pass the RequestEnvelope to Merger; Merger creates the
manifest and WaveSpec. Then Orchestrator dispatches the default first-wave
groups: **LOGS + CODE + DOCS**. Include **DATA** only for a database or
external API scope.

Route by executor mode: API → `fact-slot` / `blueprint-scout`; Cursor →
`cursor-fact-slot` / `cursor-blueprint-scout`. Checker roles are pinned to
`__MODEL_CHECKER__`; verify the picker/catalog before launch and never
silently substitute a different model.

Keep every slot narrow: one hypothesis or source and one expected fact. Use at
most **10 slots for the entire wave**, never 10 per group. Checkers verify
evidence only and write only their own immutable attempt `report.md`; Merger writes
shared evidence, state, root graph, proposals, decisions and deliveries under
`loops/<run>/**`. Later waves address documented gaps only.
Stop at root confidence ≥96%, or a structured hard blocker with one next check.

**Manual wave → Chat summary:** this command (and any USER phrase that starts a
full wave) is a **manual wave launch**. When that wave finishes (Merger +
Advocate settled), the orchestrator must auto-deliver the Chat summary from the
Merger `DeliveryPacket` — not a status-only or path-only handoff. Orchestrator
writes no files; Merger persists the summary at
`deliveries/<event_id>/chat-summary.md`. This is **not** “after every automatic
internal wave” in a continuous cascade.

Start ordinary, non-loop code requests directly; do not invoke this command for
routine implementation.

## Safety

Apply the explicit L1/L2, nginx, Docker, secrets, browser, and destructive-git
guards from `gate.yaml` and workspace rules. Finish with the Chat summary
contract above when the launched wave completes.

## Skills

`rkx-loop-core`, phase `rkx-loop-*`, KEEP: `rkx-tenets`, `graph-octocode`, `rkx-codegraph`, `octocode-code-forensics`, `rkx-mcp-utilities`, `meta-developer-tools`, `browser-ui-evidence`, `docker-diagnostics`.
