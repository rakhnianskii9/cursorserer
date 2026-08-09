---
name: android-template
description: "Reference architecture and package templates for an Expo/React Native Android operator app."
user-invocable: true
disable-model-invocation: false
---
# Android operator app — category templates (Expo / React Native)

Mobile client for the **existing** `workspace` backend.
**Do not** duplicate Gupshup/WhatsApp on the device.

**Table format:** `npm` — for `pnpm add` / `npx expo install`; **Links** — npm, GitHub, docs.

---

## MVP — product scope

| Parameter | Value |
|----------|----------|
| **Users** | 6 managers + 1 supervisor (roles/filters — clarify against the application RBAC and CRM) |
| **In MVP** | Messages · Calls · Deals and statuses · Tasks · Contacts · Notifications |
| **Outside MVP** | Bitrix widget, separate web-only CRM builder, paywall, social login |

**RKX code references (do not copy the backend vibe):**

| Domain | Where to look |
|-------|----------------|
| Chat | `packages/whatsapp/chat` |
| CRM / deals / statuses | `packages/fb-front/client/src/pages/CrmPage.tsx`, `packages/fb-front/client/src/api/crm.ts` |
| Server CRM | `packages/server/src/enterprise/routes/crm.route.ts` → `/api/v1/crm/lead-tracking` |
| Server chat | `packages/server/src/enterprise/routes/wa-chat.route.ts` |
| Web auth | `packages/ui/src/views/auth/login.jsx` |
| Mobile-infra patterns | [vibe `mobile/`](https://github.com/di-sukharev/vibe/tree/mobile) — `mobile/` only, not `backend/` |

**Expo Go is not used** — `expo-dev-client` + EAS from day one (native calls and push).

---

## RKX API map (by MVP domain)

| MVP domain | API / transport | Monorepo code |
|-----------|-----------------|----------------|
| Messages | `GET/POST /api/v1/whatsapp/chat/*`, SSE `…/stream` | `packages/whatsapp/chat/client/src/api/` |
| Calls | REST `/api/v1/gupshup/voice/*` + SIP `partner-sip.gupshup.io` (GS_SIP) | server voice branch; APK: Linphone |
| Deals / statuses | `GET /api/v1/crm/lead-tracking?workspaceId&provider=` | `crm.route.ts`, `CrmLeadTrackingService` |
| Tasks | Kommo/Bitrix through existing CRM surfaces (the `taskIds` fields in `crm.ts`, Kommo API) | `packages/fb-front/client/src/api/crm.ts`, `kommo.route.ts` |
| Contacts | CRM provider + wa-chat thread identity | `kommo_contact`, thread filters in web |
| Notifications | **new** subsystem: device token + FCM (vibe pattern) | no dedicated route yet — research |
| Auth | the application login → JWT; mobile: Bearer | `wa-chat.route.ts` → `authenticateUser` (Bearer support work) |

`EXPO_PUBLIC_API_URL` — the app's base URL.

---

## Category 1 — Application shell

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **Expo SDK** | `expo` | [docs](https://docs.expo.dev/) | APK build |
| **Expo Router** | `expo-router` | [docs](https://docs.expo.dev/router/introduction/) | `(auth)` / `(app)` / domain tabs |
| **Dev client** | `expo-dev-client` | [docs](https://docs.expo.dev/develop/development-builds/introduction/) | Native modules |
| **EAS CLI** | `eas-cli` | [docs](https://docs.expo.dev/eas/) | `eas build --profile development` |
| **Constants / linking** | `expo-constants`, `expo-linking` | [constants](https://docs.expo.dev/versions/latest/sdk/constants/) · [linking](https://docs.expo.dev/linking/overview/) | env, deep links `scheme: rkx-app` |
| **OBytes starter** | (template) | [obytes/react-native-template-obytes](https://github.com/obytes/react-native-template-obytes) | EAS + NativeWind |
| **vibe starter** | (`mobile/` folder) | [di-sukharev/vibe/tree/mobile](https://github.com/di-sukharev/vibe/tree/mobile) | auth/push/EAS patterns |
| **create-expo-app** | — | [docs](https://docs.expo.dev/get-started/create-a-project/) | `npx create-expo-app@latest -t expo-template-blank-typescript` |

**MVP navigation (tabs):** Chats · Deals · Tasks · Contacts · (call hub/shortcut from chat/deal) · Profile/notifications.

---

## Category 2 — Authentication, roles, and session

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **Secure Store (JWT)** | `expo-secure-store` | [docs](https://docs.expo.dev/versions/latest/sdk/securestore/) | Token outside AsyncStorage |
| **HTTP client** | `axios` | [axios-http.com](https://axios-http.com/) | `Authorization: Bearer`, `x-request-from: internal` |
| **Login forms** | `react-hook-form`, `zod` | [RHF](https://www.npmjs.com/package/react-hook-form) · [zod](https://www.npmjs.com/package/zod) | Same as web |
| **vibe pattern** | — | `mobile/src/lib/auth.tsx`, `token-store.ts`, `auth-bootstrap.ts` | Bootstrap, logout |

**Roles (UI research, not a new backend):** filter “my deals” (manager) vs “all managers” (supervisor) — rely on `assignedWorkspaces`, the assignee in `CrmLeadTrackingRow`, and Kommo users.

**Do not take from vibe:** `@web-app-demo/contracts`, `/api/auth/social/*`, `expo-iap`.

---

## Category 3 — Networking, cache, and shared types (cross-cutting)

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **TanStack Query** | `@tanstack/react-query` | [tanstack.com/query](https://tanstack.com/query/latest) | Same as `whatsapp/chat` and `fb-front` |
| **Zustand** | `zustand` | [GitHub pmndrs/zustand](https://github.com/pmndrs/zustand) | workspace, UI, persist |
| **Persist** | `zustand` + `@react-native-async-storage/async-storage` | [async-storage](https://www.npmjs.com/package/@react-native-async-storage/async-storage) | Hydration without login flicker |
| **SSE (chat)** | `react-native-sse` | [GitHub binaryminds/react-native-sse](https://github.com/binaryminds/react-native-sse) | `…/whatsapp/chat/stream` + Bearer |
| **SSE fallback** | `@microsoft/fetch-event-source` | [npm](https://www.npmjs.com/package/@microsoft/fetch-event-source) | POC if primary does not work |
| **Offline banner** | `@react-native-community/netinfo` | [npm](https://www.npmjs.com/package/@react-native-community/netinfo) | Wi‑Fi ↔ LTE |
| **Dates (TZ)** | `dayjs` | [npm](https://www.npmjs.com/package/dayjs) | `${TZ}` (default `UTC`) |
| **Shared types** | monorepo package | `packages/whatsapp/chat`, `packages/fb-front/client/src/api/crm.ts` | Zod/types — one import in mobile |

**Do not install on the client:** Baileys, Evolution, `whatsapp-api-js` — server only.

---

## Category 4 — Messaging (WhatsApp / `wa-chat`)

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **Inbox list** | `@shopify/flash-list` | [flash-list](https://shopify.github.io/flash-list/) | Threads, filters |
| **Chat UI** | `react-native-gifted-chat` | [GitHub FaridSafi/react-native-gifted-chat](https://github.com/FaridSafi/react-native-gifted-chat) | Message feed |
| **Chat alternative** | `@flyerhq/react-native-chat-ui` | [GitHub flyerhq/react-native-chat-ui](https://github.com/flyerhq/react-native-chat-ui) | If gifted is insufficient |
| **Keyboard** | `react-native-keyboard-controller` | [npm](https://www.npmjs.com/package/react-native-keyboard-controller) | Android input |
| **Media preview** | `expo-image` | [docs](https://docs.expo.dev/versions/latest/sdk/image/) | Cache |
| **Photo upload** | `expo-image-picker` | [docs](https://docs.expo.dev/versions/latest/sdk/imagepicker/) | Upload to the wa-chat media API |
| **Voice message** | `expo-av` | [docs](https://docs.expo.dev/versions/latest/sdk/av/) | PTT, not SIP |
| **Lightbox** | `react-native-image-viewing` | [npm](https://www.npmjs.com/package/react-native-image-viewing) | Gallery |
| **Swipe actions** | `react-native-swipe-list-view` | [GitHub jemise111/react-native-swipe-list-view](https://github.com/jemise111/react-native-swipe-list-view) | Archive / mark-read |
| **Pull-to-refresh** | RN `RefreshControl` | — | Inbox |
| **Inbox filters** | UI over API | web: `ChatSection.tsx` `matchesFilterCondition` | Web parity, no new domain logic |

**Channel strip in chat:** 24h window, template/HSM, call permission — UI; rules live on the server.

---

## Category 5 — Calls (Gupshup GS-SIP)

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **CallKeep** | `react-native-callkeep` | [GitHub react-native-webrtc/react-native-callkeep](https://github.com/react-native-webrtc/react-native-callkeep) | Incoming calls, ConnectionService |
| **InCall** | `react-native-incall-manager` | [GitHub react-native-webrtc/react-native-incall-manager](https://github.com/react-native-webrtc/react-native-incall-manager) | Speaker, proximity |
| **SIP (GS_SIP)** | `react-native-linphone-call` | [GitHub kvy-technology/react-native-linphone-call](https://github.com/kvy-technology/react-native-linphone-call) | RTP; REST for lifecycle only |
| **WebRTC** | `react-native-webrtc` | [GitHub react-native-webrtc/react-native-webrtc](https://github.com/react-native-webrtc/react-native-webrtc) | PASSTHROUGH only, not default |

`app.config.js`: CallKeep plugin, `FOREGROUND_SERVICE`, microphone. Run the SIP POC on a real Android device before polishing the UI.

**Do not use:** `@zegocloud/*` (different product).

---

## Category 6 — Deals and statuses (CRM)

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **Deal list** | `@shopify/flash-list` | see above | `GET /api/v1/crm/lead-tracking` |
| **Status / pipeline chips** | UI + TanStack Query | web: `CrmPage.tsx` `getLeadStatusMeta` | Status and pipeline filters |
| **Deal screen** | custom screen | `CrmLeadTrackingRow` in `crm.ts` | Details: status, assignee, WA link |
| **Status change** | `react-hook-form` + API provider | Kommo/Bitrix routes on server | Research the exact PATCH endpoint |
| **Kanban (optional UI)** | `@intechnity/react-native-kanban-board` | [GitHub Intechnity-com/react-native-kanban-board](https://github.com/Intechnity-com/react-native-kanban-board) | If a list plus chips is not enough |
| **DnD columns** | `react-native-draggable-flatlist` | [GitHub computerjazz/react-native-draggable-flatlist](https://github.com/computerjazz/react-native-draggable-flatlist) | Kanban alternative |
| **Horizontal columns** | `react-native-tab-view` | [docs](https://reactnavigation.org/docs/tab-view/) | Statuses as tabs |
| **UX reference** | — | [atomic-crm](https://github.com/marmelab/atomic-crm) | View only |

**Supervisor:** manager / assignee filter — a UI layer over the same `lead-tracking`.

---

## Category 7 — Tasks

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **Task list** | `@shopify/flash-list` | see above | Data from the CRM row / Kommo tasks |
| **Checkbox / done** | `react-native-paper` Checkbox or custom | [paper](https://callstack.github.io/react-native-paper/) | `crmTaskCompleted` pattern in `fbAds.ts` |
| **Deadline** | `dayjs` | see above | `crmTaskDeadline` |
| **Task form** | `react-hook-form`, `zod` | see above | Create/edit — research the endpoint |
| **Deal ↔ task link** | navigation | `taskIds` in `packages/fb-front/client/src/api/crm.ts` | Deep link from the deal screen |

---

## Category 8 — Contacts

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **CRM contact list** | `@shopify/flash-list` | Kommo/Bitrix through the CRM API | Provider parity |
| **A–Z sections** | `react-native-alphabetlist` | [npm](https://www.npmjs.com/package/react-native-alphabetlist) | Long lists |
| **Picker (minimal permissions)** | `react-native-contacts-chooser` | [GitHub bluebamboostudios/react-native-contacts-chooser](https://github.com/bluebamboostudios/react-native-contacts-chooser) | Link a phone number to a deal |
| **Expo contacts** | `expo-contacts` | [docs](https://docs.expo.dev/versions/latest/sdk/contacts/) | If full access is needed |
| **Clipboard** | `@react-native-clipboard/clipboard` | [GitHub react-native-clipboard/clipboard](https://github.com/react-native-clipboard/clipboard) | Copy number → chat/call |
| **Open chat** | `expo-router` | thread by `subscriberId` / phone | CRM → wa-chat |

---

## Category 9 — Notifications

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **Expo Notifications** | `expo-notifications` | [docs](https://docs.expo.dev/versions/latest/sdk/notifications/) | Token, permissions |
| **Device** | `expo-device` | [docs](https://docs.expo.dev/versions/latest/sdk/device/) | Push eligibility |
| **vibe pattern** | — | `push-registration.ts`, `push-navigation.ts`, `push-token-store.ts` | Register after login |
| **In-app inbox** | custom + Query | — | Notification list (if a center is needed, not just push) |
| **Badge** | `expo-notifications` setBadgeCount | [docs](https://docs.expo.dev/versions/latest/sdk/notifications/#manage-application-badge) | Unread items |

**Push types (research payload):** new message · incoming call · deal status change · new/overdue task · deal assignment to a manager.

**Server:** register/unregister device token + FCM — **new** subsystem (pattern; do not duplicate wa-chat).

**Deep link:** `rkx-app://chat/[threadId]`, `…/deal/[id]`, `…/task/[id]`, `…/call/incoming` — handled in `app/_layout.tsx` (killed → auth → target).

---

## Category 10 — UI kit, styling, and shared UI primitives

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **NativeWind** | `nativewind`, `tailwindcss` | [nativewind.dev](https://www.nativewind.dev/) | Close to fb-front Tailwind |
| **Paper** | `react-native-paper` | [callstack.github.io/react-native-paper](https://callstack.github.io/react-native-paper/) | Material: buttons, chips, dialogs |
| **Reanimated** | `react-native-reanimated` | [docs](https://docs.swmansion.com/react-native-reanimated/) | Animations |
| **Gesture Handler** | `react-native-gesture-handler` | [docs](https://docs.swmansion.com/react-native-gesture-handler/) | Swipe, DnD |
| **Safe Area** | `react-native-safe-area-context` | [npm](https://www.npmjs.com/package/react-native-safe-area-context) | Notch |
| **SVG** | `react-native-svg` | [npm](https://www.npmjs.com/package/react-native-svg) | Icons |
| **Screens** | `react-native-screens` | [npm](https://www.npmjs.com/package/react-native-screens) | Peer Router |

---

## Category 11 — Build, delivery, and observability

| Component | npm | Links | Purpose |
|-----------|-----|--------|--------|
| **Sentry** | `@sentry/react-native` | [Expo + Sentry](https://docs.expo.dev/guides/using-sentry/) | Crashes (7 operators) |
| **OTA** | `expo-updates` | [docs](https://docs.expo.dev/versions/latest/sdk/updates/) | UI fixes without Play |
| **E2E** | Maestro | [maestro.mobile.dev](https://maestro.mobile.dev/) | login → chat → call → deal |
| **i18n** | `i18next`, `react-i18next` | [npm](https://www.npmjs.com/package/i18next) | If supporting more than RU |

Distribution: EAS internal track / MDM — research separately from Play.

---

## Research categories (only gaps: mobile / Android / new push)

Do not duplicate what already exists in `wa-chat`, `crm/lead-tracking`, or Kommo/Bitrix on the server.

| # | Research category |
|---|-------------------|
| 1 | **Push + FCM:** server token registration, payload by type (message, call, deal, task) |
| 2 | **Android platform:** Doze/OEM, killed state, Foreground service + CallKeep |
| 3 | **Bearer + SSE POC** on a real device; `AppState` reconnect |
| 4 | **SIP POC:** Linphone / alternative; REST voice ↔ SIP state machine |
| 5 | **UI roles:** manager (6) vs supervisor (1) — deal/task filters without a new API |
| 6 | **Deep links** across all MVP domains + cold start |
| 7 | **Tasks:** exact read/write endpoints (from Kommo/Bitrix), not only `taskIds` in the row |
| 8 | **Deal status change** from mobile — which route already exists on the server |
| 9 | **In-app notification center** vs push only — whether a separate screen is needed |
| 10 | **Field networking:** SIP + SSE reconnect; client outbox only if the server does not queue |
| 11 | **WA rendering** of interactive elements (buttons, list) in RN |
| 12 | **EAS plugins:** CallKeep, Linphone, permissions manifest |
| 13 | **Maestro** scenarios for 7 users and an incoming call |
| 14 | **Shared package** — extract types from chat + crm |

---

## Cross-review — decisions (brief)

| Topic | Default |
|------|---------|
| SSE | `react-native-sse`; fallback `@microsoft/fetch-event-source`; Android POC on day 1 |
| KV | AsyncStorage + SecureStore; MMKV later |
| Chat UI | gifted-chat + keyboard-controller |
| Media | `expo-image`, not `react-native-fast-image` |
| Voice in chat | `expo-av` |
| JWT 401 | interceptor → refresh **if the route exists** → login |

---

## Package installation (monorepo bootstrap)

```bash
npx create-expo-app@latest packages/whatsapp/mobile -t expo-template-blank-typescript
cd packages/whatsapp/mobile

npx expo install expo-router expo-secure-store expo-constants expo-linking expo-dev-client \
  expo-image expo-image-picker expo-av expo-notifications expo-device expo-contacts

pnpm add @tanstack/react-query axios zustand @react-native-async-storage/async-storage \
  react-native-sse react-native-gifted-chat @shopify/flash-list react-native-keyboard-controller \
  react-native-callkeep react-native-incall-manager \
  react-hook-form zod dayjs react-native-paper react-native-svg \
  @react-native-community/netinfo @react-native-clipboard/clipboard

# Linphone: react-native-linphone-call — README + config plugin
eas build --profile development --platform android
```

---

## MVP checklist (work order)

1. Dev build + `scheme: rkx-app` + CallKeep plugin.
2. Auth: Bearer + SecureStore; CORS; UI roles (manager / supervisor).
3. POC: SSE + SIP on Android.
4. Messaging: inbox → chat → SSE.
5. Calls: outgoing/incoming + CallKeep.
6. Deals: `lead-tracking` list + statuses + deal screen.
7. Tasks: list + done + deal link.
8. Contacts: list + open chat/call.
9. Push: token + FCM + deep links by type.
10. Shared types package; Maestro smoke.

---
https://developer.android.com/studio/gemini/add-mcp-server for testing