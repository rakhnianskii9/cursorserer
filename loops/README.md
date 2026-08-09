# Loop runtime templates

This directory contains portable templates only. A configured workspace may
materialize a run directory here after the user explicitly starts a loop.

Do not commit live run folders, credentials, raw transcripts, or Slack
notification payloads. Keep each run correlated to one conversation and one
workspace. The stop hook must read only the matching run-scoped artifact.

## Templates

- `_models.example.md` — optional runtime model registry.
- `_registry.example.md` — loop and capability registry.
- `RUN.example.md` — run metadata template.
- `_decisions/README.md` — decision/ADR boundary.

The public archive does not claim that a model, MCP server, browser, database,
or Canvas runtime is available. Installation preflight records availability
before any optional capability is activated.
