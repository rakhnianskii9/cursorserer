# RKX run template

Copy this template to `loops/<run-id>/manifest.md` when a loop starts. Do not
put credentials, access tokens, or raw provider payloads in the manifest.

```yaml
run_id: <YYYY-MM-DD-rkx-short-problem-name>
mode: ide # ide | auto
token_mode: CURSOR # API | CURSOR
billing_credential_scope: CURSOR_SUBSCRIPTION # API_CREDENTIALS | CURSOR_SUBSCRIPTION
conversation_id: <current thread/conversation id>
problem_title: <original user-facing problem>
scope: <bounded investigation scope>
boundary:
  - read-only until the explicit implementation gate
  - no secrets or credentials in artifacts
  - no Docker rebuild/deploy without the required user gate
status: BOOTSTRAP
artifact_root: loops/<run-id>/
notification_artifact: loops/<run-id>/slack-notification.json
```

## Token-mode routing

| token_mode | billing_credential_scope | fact/preflight role | blueprint scout |
|---|---|---|---|
| `API` | `API_CREDENTIALS` | `fact-slot` | `blueprint-scout` |
| `CURSOR` | `CURSOR_SUBSCRIPTION` | `cursor-fact-slot` | `cursor-blueprint-scout` |

The caller records the mode. Never invent a mode or credential scope.

## Lifecycle values

- `BOOTSTRAP` — waiting for the initial Merger `BOOTSTRAP_WAVE_SPEC`.
- `IN_PROGRESS` — a bounded wave is running.
- `WAITING_USER` — a precise access or decision precondition is missing.
- `BLOCKED` — a confirmed recovery `HARD_BLOCKER` is terminal.
- `COMPLETED` — accepted `END` after Advocate `CLEAN` and Root-depth pass.
