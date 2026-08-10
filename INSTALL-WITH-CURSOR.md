# Install the Portable Cursor Control Plane

Attach this file to a Cursor Chat opened in the directory containing this
archive. The installation is an interactive local configuration flow. Do not
turn it into a shell installer, slash command, commit, or push.

## Install targets

Choose exactly one target before any write:

- **Project-local** — `<project>/.cursor`  
  Control plane lives inside the workspace and applies to that project only.
- **User-global** — `~/.cursor`  
  Control plane is shared across projects on this machine.

`CONTROL_PLANE_ROOT` is the chosen target directory after confirmation.
Do not materialize into both targets in one run. Do not mix project-local and
user-global files without an explicit user plan.

## Non-negotiable boundaries

- Treat the chosen install target as `CONTROL_PLANE_ROOT`.
- Do not edit the repository's plan files.
- Do not read, copy, print, or commit credentials.
- Do not modify files outside `CONTROL_PLANE_ROOT` unless the user explicitly
  confirms a path required by a selected capability.
- Do not delete legacy, project-specific, or private files. They are not part
  of this archive and must remain local to the user's environment.
- Do not run `git commit`, `git push`, `git reset`, `git restore`, `git clean`,
  or a destructive command.
- Do not overwrite an existing canonical file silently.

## Phase 1: preflight questions

Ask these questions in one compact batch and wait for the user's answers:

1. Install target: **project-local** `<project>/.cursor` or **user-global**
   `~/.cursor`? Resolve the absolute path and confirm it as
   `CONTROL_PLANE_ROOT` before any write.
2. Is the resolved `CONTROL_PLANE_ROOT` path correct for this machine?
3. Which operating system and executable paths should be used for local
   validation? Resolve them from the current runtime; never guess a home,
   system-bin, or platform-specific path.
4. Should the local stop hooks be enabled? Default: no until confirmed.
5. Should Slack delivery be enabled? Default: disabled. If enabled, ask only
   for environment variable names and destination policy; never ask the user to
   paste secret values into chat.
6. Which log locations may be read? Default:
   `CONTROL_PLANE_ROOT/runtime/logs/`. Store external locations only in the
   local install manifest.
7. Which MCP capabilities are available and approved: crash, context7,
   octocode, postgres, file access, CodeGraph, Tenets, Meta Developer Tools,
   browser, or none?
8. Which Cursor model bindings are actually available in the current picker?
   Do not infer availability from a role name or from this repository.
9. Should loop templates, browser guidance, Canvas declarations, and optional
   reference catalogs be materialized? Default: loop templates yes; optional
   capabilities only after confirmation.
10. Which timezone should portable examples use? Default: `UTC`; substitute the
    answer for `${TZ}` without changing the archive examples.

If an optional capability is unanswered or unavailable, leave it disabled and
record that fact as `unavailable` or `skipped`. Never invent a placeholder
runtime capability.

## Phase 2: inspect before writing

Before changing anything:

1. Confirm that every source path in the manifest exists.
2. Detect canonical target files and classify each as `missing`, `identical`,
   `different`, or `blocked`.
3. Show the user the target list and the files that would be backed up.
4. Stop for confirmation if any target is `different`, contains credentials, or
   is outside `CONTROL_PLANE_ROOT`.

Create a local backup directory only after confirmation:

```text
CONTROL_PLANE_ROOT/.cursor-install-backups/<UTC-timestamp>/
```

Create a local `install-manifest.json` containing the install timestamp,
archive revision, selected capabilities, source/target paths, backup paths,
placeholder substitutions, validation results, and explicit skipped
capabilities. Do not include secret values.

## Phase 3: copy confirmed archive files

This archive already uses canonical filenames. For each confirmed mapping, copy
the archive file into `CONTROL_PLANE_ROOT` as-is (no suffix stripping).

| Archive path | Runtime target |
|---|---|
| `agents/*.md` | `agents/*.md` |
| `commands/*.md` | `commands/*.md` |
| `rules/*.mdc` | `rules/*.mdc` |
| `skills/**/SKILL.md` | `skills/**/SKILL.md` |
| `skills/**/project-map.md` | `skills/**/project-map.md` |
| `skills/**/recipes.md` | `skills/**/recipes.md` |
| `skills/**/project-tenets.md` | `skills/**/project-tenets.md` |
| `hooks/*.py` | `hooks/*.py` |
| `hooks/*.sh` | `hooks/*.sh` |
| `scripts/resolve-dev-browser-url.sh` | `scripts/resolve-dev-browser-url.sh` |
| `scripts/check-dev-browser-ports.sh` | `scripts/check-dev-browser-ports.sh` |
| `hooks/rkx-slack-notify.env` | `${HOME}/.cursor/rkx-slack-notify.env` only after explicit Slack opt-in |
| `hooks.json` | `hooks.json` after path substitution |
| `CURSOR-UX.md` | `CURSOR-UX.md` |
| `CURSOR-MODELS.md` | `CURSOR-MODELS.md` |
| `RKX-LOOP-BLUEPRINT-FLOW.md` | `RKX-LOOP-BLUEPRINT-FLOW.md` |
| `reference/blueprint-index.yaml` | `reference/blueprint-index.yaml` |
| `reference/system-design-primer/**` (English bundle) | same path, including `LICENSE.txt` |
| `settings.json` | `settings.json` only after explicit settings approval |

The hook registration must replace `__CONTROL_PLANE_ROOT__` with the resolved
absolute path of this archive. Hook implementations must remain real files,
not symlinks. `rkx_write_easy_summary.py` and `rkx_lifecycle_common.py` must
be copied together into the same `hooks/` directory.

## Phase 4: configure optional capabilities

### MCP

Read `mcp.json` as a capability template, not as a ready-to-run
configuration. Build a local `mcp.json` only from capabilities confirmed in
preflight:

- remove `_publicTemplate` before writing the runtime file;
- replace every `${..._VERSION}` with a reviewed immutable version;
- replace command placeholders with executables discovered on this host;
- use `${env:NAME}`, OAuth, or Cursor prompts for secrets;
- use a read-only database URL when PostgreSQL is enabled;
- omit unavailable servers instead of leaving broken entries enabled.

### Models

Materialize the model registry only with bindings visible in the current Cursor
picker. Preserve an explicit `unavailable` record for every requested model
that cannot be verified.

### Slack

Slack is disabled by default. If enabled, the hook reads the local env file,
redacts tokens and PII, validates payload size, and fails closed for uncertain
content. A transport failure must not stop Cursor.

### Logs

Use `CONTROL_PLANE_ROOT/runtime/logs/` as the default local log contract.
External logs require an explicit user answer and are recorded as paths only.
Do not recreate private ad-hoc log files, copy raw transcripts, or put logs in
Git.

## Phase 5: validate

Run the public archive check first:

```text
python3 scripts/validate-public-control-plane.py --archive --root .
```

Then run the configured runtime check:

```text
python3 scripts/validate-public-control-plane.py --runtime --root .
```

The runtime check must include:

- canonical hook registration and path resolution;
- `python3 -B hooks/rkx_write_easy_summary.py` with empty stdin;
- imports of `rkx_lifecycle_common.py`;
- hook unit tests;
- command-to-skill and agent-to-capability references;
- WAVE_SPEC and lifecycle-artifact fixtures;
- model and MCP preflight truthfulness;
- Canvas declaration imports when Canvas is enabled.

The easy-summary smoke test must finish without
`ModuleNotFoundError`. If it fails, stop and restore the backed-up local files;
do not delete the source archive or continue to other capabilities.

## Rollback

Rollback is also an interactive Cursor Chat operation. Ask the user to confirm
the install manifest and backup directory, then:

1. restore each backed-up canonical file to its original path;
2. remove only files that the manifest says were created by this installation;
3. leave pre-existing files, credentials, examples, logs, and unrelated
   project files untouched;
4. record `rolled_back_at`, restored paths, and skipped paths in the local
   manifest.

If a backup is missing or a target has changed since installation, stop and ask
the user instead of guessing or overwriting it.

## Completion report

Return a short English report containing:

- `CONTROL_PLANE_ROOT`;
- archive revision;
- materialized files;
- skipped or unavailable capabilities;
- backup directory;
- validation commands and results;
- unresolved user decisions, if any.

Do not report secret values, full environment contents, raw Slack payloads, or
private project paths.
