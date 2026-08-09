# Loop run metadata

```yaml
schema_version: 1
run_id: <stable-run-id>
mode: ide
conversation_id: <conversation-id>
problem_title: <original-user-problem>
control_plane_revision: <archive-revision>
token_mode: API | CURSOR
capability_preflight: <path-to-local-preflight>
status: started | active | completed | blocked | failed
```

## Safety

- Keep secrets and raw transcripts out of this file.
- Store evidence under the run directory with stable references.
- Use exact `0%`–`100%` confidence values with `CONFIDENCE_BASIS`.
- A run is not a substitute for the final Chat summary.
