---
description: Resume a required RKX Boss checkpoint at wave 10 or wave 20
argument-hint: <run_id with pending CALL_BOSS>
---
# /loop-boss

Route: delegation agent `boss` (not a phase skill command).

This launcher may only resume a Merger-recorded checkpoint when the exact
  `loops/<run_id>/state/current.yaml` has `pending_action: CALL_BOSS` and
`current_wave: 10|20`. It is not an ad-hoc/manual review route. If that state is
absent, return `EXPLAIN_INVALID_RESUME` and do not invoke Boss.

Delegate only the Merger `CheckpointPacket`. Boss reads the compact state, root
graph, decision chain and disputed evidence supplied by Merger.

Challenge assumptions and return:
1. plausible alternative roots;
2. the evidence that would distinguish them;
3. exactly one highest-value next check.

Boss returns `BossPacket` only. Orchestrator forwards it to Merger; Merger
persists the packet, re-synthesizes a Proposal and routes it through Advocate.
Do not create manifests, dispatch slots, alter state, or start a wave directly.
