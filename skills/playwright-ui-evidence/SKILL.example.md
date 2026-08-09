---
name: playwright-ui-evidence
description: 'Use when UI evidence is needed: screenshots, console issues, network failures, route verification, and frontend change verification ONLY via built-in Cursor @Browser (cursor-ide-browser MCP) on the frontend dev server.'
user-invocable: true
disable-model-invocation: false
---
# UI Visual Evidence (Built-in Browser ONLY)

Skill name kept for agent-registry compatibility. **This workspace forbids external browser and Playwright/Chrome DevTools MCP for post-change UI verification.**

Canonical rule: `${CONTROL_PLANE_ROOT}/rules/browser-builtin-only.mdc`.

## Scope
- Prefer the narrowest scope possible (single page/flow).
- For frontend UI: focus on `${WORKSPACE_ROOT}/frontend/**` flows unless the
  task explicitly targets other modules.

## When to use
- “need real screenshots after the changes”
- “there are console errors”
- “check the network / 401/403/404”
- “reproduce the bug in the browser”

## Rules
- Treat as **read-only evidence** unless the parent orchestrator explicitly
  allows actions.
- Always capture:
  - URL (from `bash scripts/resolve-dev-browser-url.sh` or `.dev/forwarded-ports.env`)
  - viewport size
  - screenshots (AFTER-only for implementation verification)
  - console logs (errors/warnings) via browser tools
  - key network requests (status + URL)

## Verification path (REQUIRED)

MCP **cursor-ide-browser** only:

1. `browser_navigate` — URL from `resolve-dev-browser-url.sh` (dynamic forward from `.dev/forwarded-ports.env`, not always `:${DEV_APP_PORT}`)
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

## Dev server

```bash
cd ${WORKSPACE_ROOT}/frontend && pnpm dev
# or repo root:
cd ${WORKSPACE_ROOT} && pnpm dev
```

- Remote host listens on `127.0.0.1:${DEV_APP_PORT}`.
- Browser Tab on **client** uses forwarded local port (`bash scripts/check-dev-browser-ports.sh`).
- User authenticates manually before the verification cycle.
- Docker build is not part of this path.

## Output contract

- State that **cursor-ide-browser** / Browser Tab was used.
- If page could not load: `NOT_COLLECTED` + exact URL tried + Ports/`.dev/forwarded-ports.env` hint.
- Report shape: target route, URL, evidence tools, screenshot status, console/network summary, reproduced | verified-fixed | not-collected
