# RKX run registry

The registry is the stable contract for correlating a loop run with its
artifacts. It is intentionally small; detailed evidence belongs under the
run directory and user-facing meaning belongs in the Chat summary.

## Required run record

Every run must have:

| Field | Requirement |
|---|---|
| `run_id` | Stable filesystem-safe id = folder name: `DD-MM-YY---HH-MM---slug` under `loops/<run-id>/` |
| `conversation_id` | Exact thread/conversation id used by chat and notification delivery |
| `executor_mode` | `API` or `CURSOR`; paired with the matching billing scope |
| `mode` | `ide` or `auto` |
| `problem_title` | Original user-facing problem, not a root-hypothesis label |
| `manifest` | `loops/<run-id>/manifest.yaml` |
| `state` | canonical `loops/<run-id>/state/current.yaml` |
| `delivery` | immutable `loops/<run-id>/deliveries/<event-id>/{chat-summary.md,lifecycle.json}` |

### Mode routing

| Mode | Scope | Fact slot | Scout |
|---|---|---|---|
| `API` | `API_CREDENTIALS` | `fact-slot` | `blueprint-scout` |
| `CURSOR` | `CURSOR_SUBSCRIPTION` | `cursor-fact-slot` | `cursor-blueprint-scout` |

## Ownership

- The orchestrator owns dispatch timing and the join barrier.
- The Merger owns wave artifacts and compressed run state.
- The Advocate returns `AdvocatePacket CLEAN|HOLE`; the Boss returns
  `BossPacket`. Both are readonly and Merger persists their packets.
- A notifier consumes the exact `event_id` and lifecycle ref from a
  `DeliveryPacket`; it never chooses the newest artifact by mtime. The
  configured stop hook is the only Slack transport, so MCP delivery cannot
  duplicate it.

## Runtime policy

Run records are created and updated during a loop and remain local runtime
state. The repository commits this schema and the control-plane decisions, not
the generated run folders. Missing or mismatched run artifacts are a delivery
failure for that exact event, never a reason to read another run's state.
`WAVE_CAP` after the final wave-20 checkpoint must produce an `attention`
lifecycle event and Slack ping; notification failure never changes run state
or starts wave 21.
