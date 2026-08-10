# RKX model registry

This file records policy bindings used by the active Cursor control plane. It
does not prove which model ran a historical slot: every executed slot,
Merger, and Advocate packet must record its factual `MODEL`. Before launch,
the orchestrator verifies the exact model id in the active runtime picker/catalog.

| Role / slot family | Runtime model binding | Picker id |
|---|---|---|
| `rkx-loop` orchestrator | the verified orchestrator model | `__MODEL_ORCHESTRATOR__` |
| `fact-slot`, `cursor-fact-slot` | the verified checker model | `__MODEL_CHECKER__` |
| `blueprint-scout`, `cursor-blueprint-scout` | the verified checker model | `__MODEL_CHECKER__` |
| `merger` | the verified Merger model | `__MODEL_MERGER__` |
| `devil` / Advocate | the verified Advocate model | `__MODEL_ADVOCATE__` |
| `implementer` | the verified Merger model | `__MODEL_MERGER__` |
| manual `boss` | the verified Boss model | `__MODEL_BOSS__` |

## Recording rule

Use the actual factual model name in the artifact:

```yaml
MODEL: <model selected by the runtime>
CONFIDENCE: "<0%–100%>"
CONFIDENCE_BASIS: <cited evidence basis>
```

If the runtime did not expose the model, write `MODEL: not_recorded` and
disclose that limitation. Do not infer it from this policy file.
