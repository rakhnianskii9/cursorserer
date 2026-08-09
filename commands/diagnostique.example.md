---
description: Diagnostic five-column table
argument-hint: <object>
---
# /diagnostique

> **Cursor control-plane:** `${CONTROL_PLANE_ROOT}/` for Cursor IDE.

Diagnostic mode. The research target is whatever the USER specifies. Read-only:
no code edits.

## Goal

Identify the actual root of problems rather than treating symptoms.
Find bugs, shortcomings, violations of logic, consistency, best practices, and
technical documentation, as well as TODOs, duplicated code instead of
functions, unnecessary complexity, dead code, and discrepancies between
technical documentation and code.

## Workflow

1. Define the boundaries: which modules/files/chains are affected.
2. Read the affected code in full, not superficially.
3. If a cross-module chain exists (route → service → DB, frontend → API →
   backend, pub → sub → UI), verify it end to end, byte for byte: field names,
   types, nullability, error paths, and transformations at every boundary.
4. **ALWAYS** validate findings against technical documentation (Context7,
   fetch, internal docs). Without exceptions, every issue must be confirmed or
   refuted by a source. The only permitted exception in the “Documentation
   validation” column is “N/A — self-evident” for trivial cases (typo, dead
   code, unclosed resource).

## Output format

Table:

| Current state | What is broken and why | What to fix and how | Documentation validation | State after changes |
|---|---|---|---|---|

- “Current state” and “State after changes” describe the user journey and
  business functions, without unnecessary technical terminology.
- “What is broken” and “What to fix” must be technically precise and include
  file and line references.
- “Documentation validation” must link to a specific source (Context7, official
  docs, or internal docs), or say “N/A — self-evident”.

If everything works correctly, say so directly: “No problems found,” with a
brief description of the verified chain.
