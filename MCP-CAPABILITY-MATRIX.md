# MCP capability matrix

This matrix is a preflight template. It does not claim that any server is
installed or authenticated.

| Capability | Prerequisite | Preflight evidence | Default | Degraded behavior |
|---|---|---|---|---|
| Crash synthesis | configured Crash MCP | server responds to a read-only probe | disabled | keep cited local evidence and report synthesis unavailable |
| Context7 docs | configured docs MCP and user-approved key name | tool discovery succeeds | disabled | use local docs or ask for official docs |
| CodeGraph | local index and MCP server | index status is healthy | optional | use focused Read/search |
| Tenets | local project adapter | adapter is readable and scoped | optional | keep the direct inspection path |
| PostgreSQL | read-only URL supplied through env | connection and schema probe succeed | disabled | omit DATA slots |
| File access | approved workspace root | path-bound read-only probe succeeds | optional | use Cursor file tools |
| Meta Developer Tools | authenticated user capability | app list is available without printing secrets | disabled | use official docs and local code |
| Browser | built-in Cursor Browser Tab | navigate/snapshot probe succeeds | optional | report that UI evidence is unavailable |
| Canvas | bundled declarations and host surface | declaration import check passes | optional | return a compact Chat report |

The installer records only capability status, evidence references, and secret
environment variable names. It never stores credential values.
