---
description: RKX /loop-validate plan|diff
argument-hint: plan | diff
---
# /loop-validate

Load `rkx-loop-validate`. Validate the requested plan or diff with directly
relevant evidence and checks. If material uncertainty remains, use the wave
protocol from `rkx-loop-core` only when the USER explicitly requests a wave:
manifest, narrow evidence slots, evidence-only checker, and merger-maintained
root graph.

Do not require a fixed tool sequence, slot count, report format, or diagram.
Docker remains behind the explicit deploy gate; L1/L2 rules still apply.
