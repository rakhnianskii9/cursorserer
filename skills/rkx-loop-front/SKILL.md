---
name: rkx-loop-front
description: "Internal UI-evidence phase using Cursor's built-in browser."
argument-hint: "fast | clean"
user-invocable: false
disable-model-invocation: true
---
# rkx-loop-front

Collect UI evidence only when the request needs it. Use the built-in Cursor browser and the relevant fast or clean track; never external browsers or credentials in artifacts.

## Protocol

Use `browser-ui-evidence`. A single targeted browser check may be sufficient.
A wave (`rkx-loop-core`) starts only when the USER explicitly requests one. On
phase conclusion deliver **Chat summary ALWAYS** from `rkx-loop-core` (5 parts).
