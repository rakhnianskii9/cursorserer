---
name: rkx-loop-validate
description: "Internal plan or diff validation phase for RKX work."
argument-hint: "plan | diff"
user-invocable: false
disable-model-invocation: true
---
# rkx-loop-validate

Validate the requested plan or diff with proportionate, relevant checks. Diff validation occurs after L2 work; Docker remains behind the explicit Ship gate.

## Protocol

Use direct targeted Read/search first. Use Tenets only for unknown scope after that; use CodeGraph/Octocode only for structural gaps; use logs, docs, and data only when relevant.

Molecule 11 (revert-first by diff) applies when validate(diff) is red. A wave
(`rkx-loop-core`) starts only when the USER explicitly requests one. On
validation conclusion deliver **Chat summary ALWAYS** from `rkx-loop-core`
(5 parts).

When a Slack notification is needed, persist only the safe lifecycle artifact
defined by `rkx-loop-core` under `loops/<run>/slack-notification.json`.
Preserve the original problem title and conversation correlation; do not copy
raw logs or the full Chat summary into the artifact. The stop hook owns the
lifecycle card, while MCP may deliver the full verdict only after
`chat_itog_delivered`.
