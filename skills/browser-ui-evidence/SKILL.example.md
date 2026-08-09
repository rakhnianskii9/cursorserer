---
name: browser-ui-evidence
description: 'Use when UI evidence is needed: screenshots, console issues, network failures, route verification, and frontend change verification ONLY via built-in Cursor @Browser (cursor-ide-browser MCP). Dual-track: fast local Vite or clean prod.'
user-invocable: true
disable-model-invocation: false
---
> **Cursor control plane:** `${CONTROL_PLANE_ROOT}/` is the active RKX control plane for Cursor sessions; use `cursor-ide-browser` / @Browser here.

# UI Visual Evidence (Built-in Browser ONLY)

**This workspace forbids external browser and Playwright/Chrome DevTools MCP for post-change UI verification.**

Always-on guardrail: `${CONTROL_PLANE_ROOT}/rules/rkx-always-on.mdc` (Browser). This skill is the procedure.

Used by **rkx-loop-front** / **RKX-Loop** (`/loop-front`, validate_ui slot). Treat as **read-only evidence** unless the parent loop phase explicitly allows interactions.

## Scope

- Prefer the narrowest scope possible (single page/flow).
- For frontend UI: focus on `${WORKSPACE_ROOT}/frontend/**` unless the task explicitly targets other modules.

## When to use

- “need real screenshots after the changes”
- “there are console errors”
- “check the network / 401/403/404”
- “reproduce the bug in the browser”

## Dual-track verification

| Track | URL | When |
|---|---|---|
| **Fast (local Vite)** | from `bash scripts/resolve-dev-browser-url.sh` or `.dev/forwarded-ports.env` | Default for frontend / auxiliary dev changes |
| **Clean (prod)** | `https://${PUBLIC_HOST}/` | Post-gate prod sanity; only after loop allows clean track |

**Fast track ports:** primary app `${DEV_APP_PORT}`; auxiliary modules `${AUX_APP_PORT_A}`–`${AUX_APP_PORT_C}`. Remote host listens on `127.0.0.1`; Browser Tab on **client** uses forwarded local port (`bash scripts/check-dev-browser-ports.sh`).

**Clean track credentials:** read from the local `.env` source only (`${WORKSPACE_ROOT}/.env`): `${BROWSER_LOGIN}` and `${BROWSER_PASSWORD}`. The agent may autonomously authenticate the clean-track Browser Tab with those credentials when the tab is not already authenticated. **Never** write password values into skills, run ledgers, git, tool descriptions, screenshots, console output, or chat.

## Rules

Always capture:

- URL tried
- track (fast | clean)
- viewport size
- screenshots (AFTER-only for implementation verification)
- console logs (errors/warnings) via browser tools
- key network requests (status + URL)

## Verification path (REQUIRED)

MCP **cursor-ide-browser** only:

1. `browser_navigate` — fast URL from `resolve-dev-browser-url.sh`, or clean prod URL from plan SoT
2. `browser_snapshot`
3. `browser_take_screenshot` when a visual artifact is required

Optional lock workflow: `browser_lock` → interactions → `browser_unlock`.

**FORBIDDEN in this workspace:**

- Playwright MCP / `run_playwright_code`
- Chrome DevTools MCP
- `xdg-open`, `open`, external Chrome/Safari/Edge
- «Open in Browser» from Ports panel
- Simple Browser as user-facing workaround

If navigation fails on `http://localhost:${DEV_APP_PORT}/`, report: use **Forwarded Address** from View → Ports or update `.dev/forwarded-ports.env` — do not suggest external browser.

## Authentication

- Reuse an existing authenticated Browser Tab when available; do not reload it merely to authenticate.
- For an unauthenticated **clean** track, read `RKX_BROWSER_LOGIN` and `RKX_BROWSER_PASSWORD` from the local `.env` source and fill the login form through `cursor-ide-browser` only.
- Never expose, echo, log, screenshot, or persist the credentials. Do not use clean-track credentials on local/fast URLs.
- Stop and report if MFA, CAPTCHA, a manual takeover, or an unexpected account-selection screen appears.

## Dev server (fast track)

```bash
cd ${WORKSPACE_ROOT}/frontend && pnpm dev
# or repo root:
cd ${WORKSPACE_ROOT} && pnpm dev
```

- Fast-track authentication is user-owned; use the local/mock role or an already authenticated local session.
- Docker build is not part of this path.

## Output contract

- State that **cursor-ide-browser** / Browser Tab was used.
- State track: **fast** or **clean**.
- If page could not load: `NOT_COLLECTED` + exact URL tried + Ports/`.dev/forwarded-ports.env` hint (fast) or plan SoT hint (clean).
- Report shape: target route, URL, track, evidence tools, screenshot status, console/network summary, reproduced | verified-fixed | not-collected
