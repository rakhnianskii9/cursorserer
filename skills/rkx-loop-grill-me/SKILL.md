---
name: rkx-loop-grill-me
description: "Internal clarification phase for explicit RKX work."
argument-hint: "<goal>"
user-invocable: false
disable-model-invocation: true
---
# rkx-loop-grill-me

Ask only questions that materially affect scope, success criteria, risk, or delivery. This is L1 and never authorizes product edits.

## Protocol

Do not require a wave when direct clarification resolves the uncertainty. A
wave (`rkx-loop-core`) starts only when the USER explicitly requests one.
While awaiting USER answers, ask only the material questions and wait; do not
emit a terminal Chat summary. A clarification phase does not produce the
five-part verdict and does not start a wave. `rkx-loop-core` may deliver its
full Chat summary only after an explicitly terminal wave or phase conclusion.
