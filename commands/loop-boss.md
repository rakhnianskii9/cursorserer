---
description: Manually challenge an RKX wave investigation
argument-hint: <scenario or run state>
---
# /loop-boss

Route: delegation agent `boss` (not a phase skill command).

Manual use only. This launcher delegates the review to the internal `boss` role. It reads the
scenario, compressed state, root graph, and disputed evidence supplied by the
current investigation.

Challenge assumptions and return:
1. plausible alternative roots;
2. the evidence that would distinguish them;
3. exactly one highest-value next check.

Do not create manifests, dispatch slots, alter state, or start a wave. This
command is an adversarial review input for the orchestrator, not an
orchestrator.
