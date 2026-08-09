# Runtime logs

This directory is the default local log contract for the portable control
plane. Runtime logs are generated data and must never be committed.

- Keep logs under this directory only when the user has approved the source.
- Redact tokens, credentials, contact data, and raw provider payloads.
- Use external log paths only when they are recorded in the local install
  manifest.
- Do not recreate private ad-hoc log files or copy complete chat transcripts.
