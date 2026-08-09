---
name: rkx-loop-full
description: "Internal coordinator for explicit RKX investigation and delivery phases."
argument-hint: "<slug> <goal>"
user-invocable: false
disable-model-invocation: true
---
# rkx-loop-full

Use the necessary phases only: clarify, investigate, plan, validate, then stop at L1 until the user supplies an explicit L2 request.

## Protocol

Start with targeted inspection. Load `rkx-loop-core` and run the wave protocol
only when the USER explicitly requests a wave or `/rkx-loop` / `/loop-bug`
scope applies. Preserve L1/L2, nginx pre-copy, secret, destructive-Git, and the
Docker `Ship` gate.

On L1 STOP / phase conclusion deliver **Chat summary ALWAYS** from
`rkx-loop-core` (5 parts).

For Slack lifecycle updates, preserve the original user goal as
`problem_title` and use the run-scoped notification artifact from
`rkx-loop-core`. The stop hook owns the short card; MCP may send a separate
full verdict only after `chat_itog_delivered`. Never derive either message
from an unrelated or globally newest `state.md`.
