---
name: meta-developer-tools
description: >-
  Routes Meta Developer Tools MCP (server `user-Meta Developer Tools`) for Facebook/Meta
  app ops: app list/settings, rate limits, call volume, deprecations, app review, compliance,
  webhook list/subscribe/test, and Meta docs/changelog search. Use when the user mentions Meta
  Developer Tools, Facebook/Meta app config, Graph API health, rate limits, App Review,
  compliance/violations, webhook subscriptions/fields/verify, or Meta developer docs/changelog.
  Pair with host security guidance for tokens/webhooks. Not for browser
  DevTools or IDE diagnostics.
user-invocable: true
disable-model-invocation: false
---

# Meta Developer Tools MCP

**Server:** `user-Meta Developer Tools`  
**Contract:** `GetMcpTools` once per session for this server → then `CallMcpTool`. Do **not** re-discover mid-task.  
**App id SoT:** env key `FACEBOOK_APP_ID` (never print value). If unknown → `devtools_app_list` `action=list`.

## Boot (always, ≤2 calls)

1. If tools fail with auth → `mcp_auth` (empty args) once, then retry. Do not loop.
2. Resolve `app_id` (env key or list). Cache for the turn.
3. Route by intent table below. **Parallelize** independent reads in one batch.

## Intent → tool (one hop)

| Intent | Tool | action | Required extras |
|---|---|---|---|
| Which apps / missing app | `devtools_app_list` | `list` | optional `limit`/`cursor` |
| App basic/advanced/security/restrictions/DPO | `devtools_app` | `basic_settings` \| `advanced_settings` \| `security` \| `restrictions` \| `data_protection_officer` | `app_id` |
| Rate-limit health | `devtools_api_usage` | `rate_limits` | `app_id` |
| Call volume / endpoint burn | `devtools_api_usage` | `call_volume` | `app_id`; opt `lookback_minutes` (1–43200, def 1440), `endpoint` |
| Platform deprecations | `devtools_api_usage` | `deprecations` | `app_id` |
| App Review status/history/privileges/reqs | `devtools_app_review` | `status` \| `history` \| `privileges` \| `requirements` | `app_id` |
| Compliance / violations | `devtools_compliance` | `status` | `app_id` |
| Webhook topics available | `devtools_webhook_list` | `list_topics` | `app_id` |
| Current webhook subs | `devtools_webhook_list` | `list_subscriptions` | `app_id` |
| Subscribe webhook | `devtools_webhook_manage` | `subscribe` | `app_id`,`topic`,`callback_url`,`verify_token`,`fields[]`; opt `include_values` |
| Unsubscribe | `devtools_webhook_manage` | `unsubscribe` | `app_id`,`topic` |
| Add/remove webhook fields | `devtools_webhook_manage` | `update_fields` | `app_id`,`topic` + `add_fields[]` and/or `remove_fields[]` |
| Fire test webhook | `devtools_webhook_test` | `test_send` | `app_id`,`topic`,`field` (must be active sub) |
| Meta docs search | `devtools_discovery` | `search_docs` | `query`; opt `max_results` 1–20 (def 5), `offset` |
| Changelog products/URLs | `devtools_api_changelog` | `list_products` \| `get_changelog_url` \| `get_rss_url` | `product` for rss; opt for changelog url |

Optional on every call: `model_name` (observability only — skip unless asked).

## Parallel playbooks (default batches)

**Health dig** (one batch after app_id):
```
rate_limits + call_volume + deprecations + compliance/status + app/basic_settings
```

**Webhook dig** (read-only first):
```
list_subscriptions + list_topics
→ if test needed: test_send(topic, field from active sub)
→ manage ONLY after USER confirms callback_url + verify_token + fields
```

**Review dig:**
```
app_review/status + privileges + requirements + compliance/status
```

**Docs dig** (no app_id):
```
discovery/search_docs + changelog/list_products (then get_changelog_url/get_rss_url)
```

## Hard gates

| Op | Rule |
|---|---|
| `webhook_manage` subscribe/unsubscribe/update_fields | **USER confirm** first. Live HTTPS callback that passes Meta verify. Never invent `verify_token` — use env key name `FACEBOOK_WEBHOOK_VERIFY_TOKEN` / aliases from code, do not echo value. |
| Secrets / tokens / app secret | Never print. Report key names only. |
| Frozen/restricted apps | `basic_settings` / `compliance` / `app_list` still work; expect `status.state` = `restricted` \| `deactivated`. |
| Missing app in list | Likely consent not granted to DevTools MCP — tell USER to grant on Meta consent screen; do not assume app deleted. |
| Rate status decode | `healthy`<70 · `warning`≥70 · `critical`≥90 · `throttled`@100 · `unmetered`. `call_volume.usage_rate` >1.0 = throttling. |
| This MCP ≠ browser DevTools / IDE diagnostics | Never route Cursor/browser issues here. |
| Code forensics | Focused Read/search first; Tenets only for unknown scope and CodeGraph/Octocode only for a structural gap. This MCP is for **live Meta app state**, not for reading our TS. |

## Repo anchors (when correlating MCP ↔ code)

- Env key names only: `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`,
  `FACEBOOK_WEBHOOK_VERIFY_TOKEN` (never print values).
- Correlate MCP state with the host app's Meta/Facebook webhook, OAuth, and
  marketing modules via focused local search. Do not assume a fixed product
  path layout.
- This MCP is for **live Meta app state**, not a substitute for reading local
  TypeScript.

## Output contract (short)

Report only: `app_id` (masked ok), actions run, key fields (`overall_status`, usage %, cooling_down_minutes, subscription topic/fields, review/compliance blockers, doc URLs). Next action = one concrete Meta console / code / USER step. No dump of full JSON unless USER asks.

## Degradation

`[DEGRADED: meta-devtools-unavailable]` → docs/changelog via `devtools_discovery`/`devtools_api_changelog` if still up; else official developers.facebook.com + local code/env. Never fake live rate/review/webhook state.
