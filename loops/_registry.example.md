# Capability registry

The registry records what the installation preflight can actually use.

```yaml
schema_version: 1
capabilities:
  browser:
    status: unverified
    required_evidence: cursor-ide-browser
  canvas:
    status: unverified
    required_evidence: canvas-sdk
  mcp:
    status: unverified
    required_evidence: local-mcp-config
  logs:
    status: ready
    default_root: runtime/logs
  slack:
    status: disabled
    required_evidence: user-confirmed-secret-env
```

Allowed statuses are `ready`, `disabled`, `unavailable`, and `unverified`.
Every enabled capability must have a local evidence reference.
