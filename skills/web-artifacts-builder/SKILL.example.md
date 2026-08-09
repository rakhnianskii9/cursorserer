---
name: web-artifacts-builder
description: 'Use only for isolated artifact, prototype, or demo generation; keep it separate from production module conventions.'
user-invocable: true
disable-model-invocation: false
---
# Web Artifacts Builder (optional)

This example is disabled until the user approves a reviewed tool source and
version. It is not part of the default production workflow.

## Scope

- prototypes
- demos
- isolated artifacts
- throwaway exploration that should not redefine production UI conventions

Do not use this skill for production module work unless the user explicitly
asks for an isolated artifact or demo.

## Quick Start

1. Ask the user which reviewed artifact tool and immutable version should be
   used.
2. Run its documented local command only after the user confirms the output
   directory and network policy.
3. Keep the generated artifact outside production source directories.

## What this skill does

- Uses only a reviewed, pinned tool source after explicit opt-in.
- Does not fetch mutable `latest` assets.
- Keeps generated output in a temporary or user-selected artifact directory.

## Notes

- Requires Node.js 18+ and internet access when running scripts.
- If your environment blocks outbound network, run scripts in an environment with GitHub access.
- Production stack rules still win: this skill must not silently override the
  target project's module boundaries.
