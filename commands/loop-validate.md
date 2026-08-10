---
description: RKX /loop-validate plan|diff
argument-hint: plan | diff
---
# /loop-validate

Load `rkx-loop-validate`. Validate the requested plan or diff with directly
relevant evidence and checks. If material uncertainty remains, use the wave
protocol from `rkx-loop-core` only when the USER explicitly requests a wave:
manifest, narrow evidence slots, evidence-only checker, and merger-maintained
root graph.

Do not require a fixed tool sequence or unconditional slot-count floor.
Return the focused validation result. Emit the five-part summary only when an
explicitly requested wave reaches a terminal decision. Molecule 11 applies on
red validate(diff).
Docker remains behind the explicit Ship gate; L1/L2 rules still apply.

For Slack, write a run-scoped lifecycle artifact with the original
`problem_title`, current `conversation_id`, `event_id`, validation status,
user-facing summary, and one next action. The stop hook sends that short card;
only an actually delivered full Chat summary may be sent separately through MCP.
