# RKX run registry

The registry is the stable contract for correlating a loop run with its
artifacts. It is intentionally small; detailed evidence belongs under the
run directory and user-facing meaning belongs in the Chat summary.

## Required run record

Every run must have:

| Field | Requirement |
|---|---|
| `run_id` | Stable filesystem-safe id, matching `loops/<run-id>/` |
| `conversation_id` | Exact thread/conversation id; Slack stop-hook matching is optional outside Cursor |
| `token_mode` | `API` or `CURSOR`; paired with the matching billing scope and recorded by the caller |
| `mode` | `ide` or `auto` |
| `problem_title` | Original user-facing problem, not a root-hypothesis label |
| `manifest` | `loops/<run-id>/manifest.md` |
| `state` | `loops/<run-id>/state.md` |
| `notification` | `loops/<run-id>/slack-notification.json` |

### Mode routing

| Mode | Scope | Fact slot | Scout |
|---|---|---|---|
| `API` | `API_CREDENTIALS` | `fact-slot` | `blueprint-scout` |
| `CURSOR` | `CURSOR_SUBSCRIPTION` | `cursor-fact-slot` | `cursor-blueprint-scout` |

## Ownership

- The orchestrator owns dispatch timing and the join barrier.
- The Merger owns wave artifacts and compressed run state.
- The Advocate returns an `ATTACK_PACKET` only and never writes this registry
  or any `loops/**` artifact.
- The stop-hook reads only the matching run-scoped notification artifact.

## Runtime policy

Run records are created and updated during a loop and remain local runtime
state. The repository commits this schema and the control-plane decisions, not
the generated run folders. Missing or mismatched run artifacts are a
fail-open notification condition, never a reason to read another run's state.
