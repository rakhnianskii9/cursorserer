---
description: Lightweight RKX investigation and implementation workflow
argument-hint: <slug> <goal> [--skip-grill]
---
# /loop-full

> **Cursor control-plane:** `${CONTROL_PLANE_ROOT}/` for Cursor IDE.

Load `rkx-loop-full`. This is a direct focused phase helper, not a wave entry
point; use `rkx-loop-core` only when the USER explicitly requests a wave.

USER arguments: `<slug> <goal> [--skip-grill] [--mode auto]`.

Start with targeted inspection and carry out the requested diagnosis or plan.
L2 implementation requires an explicit user L2 gate, then delegation to the
internal **implementer** agent; the read-only orchestrator must never carry out
product edits. Use phases, a run directory, additional tools, or subagents only
if they make the work clearer. Preserve L1/L2, nginx backup, explicit Docker
Ship gate, secrets, and destructive-git safety rules. On L1 STOP / phase
conclusion return the focused result. Emit the five-part summary only if an
explicitly requested wave reaches a terminal decision.

For Slack, keep the original user goal as `problem_title` and write the
run-scoped lifecycle artifact defined by `rkx-loop-core`; the stop hook sends
the short card, while a full verdict is sent separately only after the
complete Chat summary exists.
