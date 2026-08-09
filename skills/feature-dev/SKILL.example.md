---
name: feature-dev
description: 'Use when implementing or reviewing a medium/large feature in this monorepo: scope mapping, module boundaries, migrations, non-Docker build validation, rollback notes, and production-ready delivery.'
user-invocable: true
disable-model-invocation: false
---

**CodeGraph:** the `.codegraph/` index and `codegraph_*` MCP are available for structural navigation through `workspace-codegraph` (+ `octocode-code-forensics`); do not start with grep.

# Feature Dev

Use this skill for medium/large feature work in this repository when the task spans more than one file, more than one layer, or has migration/runtime risk.

## Trigger Phrases

Load this skill when the task is about:
- a new feature or substantial enhancement
- multi-file implementation across `server`, `components`, `fb-front`, `ui`, or `whatsapp`
- new route/service/entity/flow
- migration-backed data model changes
- rollout risk, rollback planning, or build validation

## Scope Map

- `packages/server` — Node/TS, TypeORM, PostgreSQL, Redis, BullMQ
- `packages/components` — the application nodes and tooling
- `packages/fb-front` — React/Vite/Tailwind/Flowbite
- `packages/ui` — React/MUI
- `packages/whatsapp/**` — React frontends and related flows
- `docker`, `nginx` — infra/runtime wiring only when explicitly in scope

## Source of Truth Order

1. Existing implementation in the codebase
2. Internal docs under `${WORKSPACE_ROOT}/docs`
3. External docs only after stack/version reality is understood

## Workflow (Required)

1. Define exact scope and touched modules before coding.
2. Search for existing patterns and nearest in-repo analogues before introducing a new abstraction.
3. Prefer minimal blast radius and preserve current module boundaries.
4. Implement production code, not scaffolding or placeholders.
5. If schema/entity changed, add and register a migration in `packages/server/src/database/migrations/postgres/index.ts`.
6. Run non-Docker build validation for touched package(s) using the real `package.json.name` filter.
7. For risky DB/infra/config changes, provide a short rollback note.
8. If user-visible behavior changed, check whether existing docs under `${WORKSPACE_ROOT}/docs` must be updated.

## Hard Rules

- Do not treat `pnpm test` as default validation in this repo. It is opt-in and requires explicit user request.
- Docker rebuild is out of scope unless the user explicitly asks for it.
- Do not create more than one general `.md` for a new module.
- Do not create a new module doc until absence of a relevant existing doc is verified.
- Respect existing UI stack boundaries: `fb-front` uses Flowbite/Tailwind, `ui` uses MUI.

## Required Evidence

- touched files and why they were touched
- build command(s) actually run
- build result for touched package(s)
- migration registration evidence when schema changed
- non-functional notes: perf, observability, config hygiene, rollback safety

## Output Contract

Return:
- modified files
- build results only for validations actually run
- migration/DB note or `N/A`
- risk notes (perf/observability/config/data safety)
- rollback note for risky changes or `N/A`
- next actionable step
