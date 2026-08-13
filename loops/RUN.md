# RKX run template

Copy this template to `loops/<run-id>/manifest.yaml` when Merger bootstraps a
run. Do not put credentials, access tokens, or raw provider payloads in the
manifest. Canonical current pointer is `state/current.yaml`.

```yaml
run_id: <DD-MM-YY---HH-MM---slug>  # MUST equal folder name
mode: ide # ide | auto
executor_mode: CURSOR # API | CURSOR
token_mode: CURSOR # alias of executor_mode; API | CURSOR only
billing_credential_scope: CURSOR_SUBSCRIPTION # API_CREDENTIALS | CURSOR_SUBSCRIPTION
continuation_policy: ONE_WAVE # ONE_WAVE | CONTINUOUS
implementation_authorized: false
conversation_id: <current thread/conversation id>
correlation_id: <request correlation id>
problem_title: <original user-facing problem>
scope: <bounded investigation scope>
boundary:
  - read-only until implementation_authorized or explicit L2 gate
  - no secrets or credentials in artifacts
  - no Docker rebuild/deploy without the required user gate
artifact_root: loops/<run-id>/
state_pointer: loops/<run-id>/state/current.yaml
```

## Token-mode routing

| executor_mode | billing_credential_scope | fact/preflight role | blueprint scout |
|---|---|---|---|
| `API` | `API_CREDENTIALS` | `fact-slot` | `blueprint-scout` |
| `CURSOR` | `CURSOR_SUBSCRIPTION` | `cursor-fact-slot` | `cursor-blueprint-scout` |

CODEX is absent from active routing. The caller records the mode. Never invent
a mode or credential scope.

## Wave budget

```yaml
current_wave: 0..20
boss_checkpoint_every: 10
wave_cap: 20
max_slot_attempts: 2
max_slots_per_wave: 10
```

## Lifecycle / investigation_status

- `BOOTSTRAP` — Merger creating initial WaveSpec.
- `ACTIVE` — a bounded wave is running.
- `PAUSED_AFTER_WAVE` — ONE_WAVE policy delivered after a wave.
- `WAITING_USER` — off-host / scope decision / WAVE_CAP after exhausted host RO.
- `BLOCKED` — accepted `HARD_BLOCKER`.
- `CONCLUDED` — accepted `END`.

## Preflight

CapabilityPacket slot statuses: `READY | UNAVAILABLE | STALE | INVALID`.
Merger PreflightDecision: `DISPATCH | REPLAN | WAITING_USER | HARD_BLOCKER_CANDIDATE`.
See `.cursor/schemas/preflight-v1.json` and
`.cursor/schemas/packets/capability-packet-v1.json`.
