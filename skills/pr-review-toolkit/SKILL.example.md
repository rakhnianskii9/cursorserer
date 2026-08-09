---
name: pr-review-toolkit
description: 'Use when reviewing changes for correctness, regressions, migrations, evidence coverage, security, and operability in this monorepo before approval or merge.'
user-invocable: true
disable-model-invocation: false
---

**CodeGraph:** the `.codegraph/` index and `codegraph_*` MCP are available for structural navigation through `rkx-codegraph` (+ `octocode-code-forensics`); do not start with grep.

# PR Review Toolkit

Use this skill to review a change set before merge.

## Review lenses

- Correctness vs acceptance criteria
- Regression risk across touched modules
- Migration/data safety (TypeORM, FK/type alignment, migration registration)
- Security issues (injection, unsafe HTML, auth/session exposure, secret handling)
- Non-functional impact (performance, logging/observability, rollback readiness)
- Evidence coverage: is the claimed fix actually supported by fresh verification

## Required checks

1. Read only changed files and key usages.
2. Verify build signal for touched module(s).
3. Verify that any runtime/UI/DB claim is backed by current evidence or explicitly marked `N/A`.
4. Flag docs drift when behavior changed but docs did not.
5. If scope is runtime/backend, require docker/runtime evidence when the change claims operational safety.

## E2E chain validation (when applicable)

When the change crosses module boundaries (route → service → DB, frontend → API → backend, event publisher → subscriber → UI), trace the full chain byte-by-byte:

1. Map the data flow: entry point → transformations → persistence/output.
2. At each boundary verify: field names match, types align, nullability is consistent, error paths propagate correctly.
3. Present as a table: **Current state** → **What is broken and why** → **What to fix and how** → **Technical-documentation validation** → **State after the fix**.
4. If chain is intact, state explicitly: "E2E chain verified, no breaks found" with evidence.

## Review Verdict Policy

- `APPROVED` — requirements met, evidence sufficient, no material unclosed risk
- `NEEDS_REVISION` — code may be close, but evidence is missing or a material gap remains
- `FAILED` — critical correctness, security, migration, or operability issue

## Output format

- Status: APPROVED | NEEDS_REVISION | FAILED
- Blocking issues (CRITICAL/MAJOR)
- Non-blocking improvements (MINOR)
- Exact next step to reach APPROVED
