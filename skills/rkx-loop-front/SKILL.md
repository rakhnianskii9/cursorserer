---
name: rkx-loop-front
description: "Internal UI-evidence phase using Cursor's built-in browser."
argument-hint: "fast | clean"
user-invocable: false
disable-model-invocation: true
---
# rkx-loop-front

Collect UI evidence only when the request needs it. Use the built-in Cursor browser and the relevant fast or clean track; never external browsers or credentials in artifacts.

## Evidence protocol

Follow `rkx-loop-core` when this phase needs an explicit wave. The readonly Orchestrator passes the RequestEnvelope to Merger, runs preflight, and dispatches all independent READY slots as one parallel batch. A wave has at most 10 slots total across LOGS/CODE/DOCS/optional DATA/Scout groups; every slot has one hypothesis, source, expected fact, and expected decision change. Merger alone writes shared artifacts and settles join → Proposal → Advocate → AcceptedDecision.

Later waves target only recorded gaps. Accepted NEXT after wave 10 must pass Boss → Merger re-synthesis → Advocate before wave 11. Accepted NEXT after wave 20 must pass the final Boss/Merger/Advocate checkpoint and then become `WAITING_USER/WAVE_CAP` with Slack attention; wave 21 is forbidden.

Use direct targeted Read/search first. Use Tenets only for unknown scope after that; use CodeGraph/Octocode only for structural gaps; use logs, docs, and data only when relevant.

A single targeted browser check may be sufficient; no fixed wave or report is required.
