# 🧙‍♂️✨💫 CURSORCERER

> **Ready-Made Debugging Blueprint Control Plane for Cursor: Agents, Commands, Rules, Skills, Hooks, Schemas & Validators in [1] Loop**

![Ready-made blueprints](https://img.shields.io/badge/ready--made-%F0%9F%93%98%20blueprints-2563EB?style=flat-square&labelColor=334155)
![Install in minutes](https://img.shields.io/badge/install%20in-%F0%9F%9A%80%20minutes-EA580C?style=flat-square&labelColor=334155)
![Declarative investigation loops](https://img.shields.io/badge/declarative-%F0%9F%94%84%20loops-0284C7?style=flat-square&labelColor=334155)
![Slack preflight escalation](https://img.shields.io/badge/slack-%F0%9F%94%94%20preflight-CA8A04?style=flat-square&labelColor=334155)
![Schema-backed validation](https://img.shields.io/badge/schemas-%E2%9C%85%20validate-15803D?style=flat-square&labelColor=334155)

---

## 🔥 What It Is

**A control plane that turns a symptom into a provable root cause.**

```text
Symptom
   → Parallel evidence
   → Confidence + CONFIDENCE_BASIS
   → Chat summary
   → Explicit L2 gate
   → Code change / validate(diff)
```

The output is a decision with an evidence trail — not a model answer from thin air.
Code changes happen only when the original request authorized them, or after an explicit Smash gate.

---

## 💡 How It Works

Root-cause search is not hidden inside agent magic. **Before launch, the system describes:**

```text
The problem → Working scope → Hypotheses
                                      ↓
Decision-change criteria ← Expected facts ← Evidence sources
        ↓
Stop condition → Required capabilities → Escalation conditions
```

**☝🏼 The agent must show:**
- What it is checking
- Why it is checking it
- Which facts it expects
- How those facts will change the decision
- What happens if the evidence is unavailable

---

## ✈️ Preflight

**Before capability-dependent work starts**, the system checks what is actually available. Typical capabilities include:

```text
tools    models    browser    logs    mcp    slack    database    api access
```


**Preflight resolves into:**

```text
ready    waiting_user    blocked    replan
```

<br>

- `READY` → Dispatch
- `REPLAN` → Merger new spec revision
- `WAITING_USER` / `BLOCKED` → Check as-is · Provide · Stop
- Slack is optional and is not required for this decision.

```text
USER: symptom / task
        │
        ▼
preflight  (tools · models · browser · logs · mcp · slack · database · api access)
        │
        ├── READY         → Dispatch (full or degraded)
        ├── WAITING_USER ─┐
        ├── BLOCKED      ─┴→ Cursor: Check as-is · Provide · Stop
        │                      ├── Check as-is → Dispatch (may be degraded)
        │                      ├── Provide     → wait → preflight again
        │                      └── Stop        → no dispatch
        └── REPLAN        → Merger new spec revision

```

---

## 🔄 RKX Loop

1. **RKX Loop is the main automated investigation workflow.** Each wave consists of independent narrow slots:
- `LOGS` — facts from logs
- `CODE` — facts from code
- `DOCS` — contracts and documentation
- `DATA` — database and API, only when they are in scope
- `BLUEPRINT-SCOUT` — search for matching reference entries

2. **After the slots finish, Merger:**

```text
Saves evidence packets → Merges facts → Records contradictions
                                                         ↓
Evaluates confidence + CONFIDENCE_BASIS ← Checks Root-depth ← Updates the root graph
        ↓
Emits a Proposal → Advocate (CLEAN / HOLE) → NEXT_WAVE_SPEC / END / HARD_BLOCKER
```

3. **Advocate checks the leading root** and looks for alternative explanations, weak points, and unconfirmed transitions. Important outcomes include:
- `CLEAN`
- `HOLE`

When the hole is material, Merger revises one concrete next check instead of starting an endless argument between agents. When the investigation reaches L1 Stop, Cursor delivers the Chat summary. It contains:

- Business / UI statement
- Five-column evidence table
- Technical facts
- Structure diagram
- ✅ or ❌ verdict · Causal chain · Basis · Where

```text
Chat summary  ≠  loops/<run>/ artifacts
        │
        ▼
Smash → Build → validate(diff) → optional Ship
```

```text
bootstrap → preflight → parallel fan-out → merge → advocate
        │
        ├── NEXT_WAVE_SPEC → another wave (Boss at 10 / 20)
        ├── END            → L1 Chat summary
        └── HARD_BLOCKER   → recovery or Stop
                │
                ▼
         Smash → Build / validate(diff) → optional Ship
```

---

## 💎 What You Get

### 📘 Ready-Made Debugging Blueprint Control Plane

Instead of manually assembling the process from prompts, roles, and rules every time, the user gets ready-made scenarios:

```text
Bug investigation → Root-cause search → Fix planning
                                              ↓
UI / Browser evidence ← Diff validation ← Plan validation
        ↓
Design → Implementation → Validation / deploy gates → Reference coverage
```

**Each blueprint defines:**
- Which roles take part
- Which evidence is required
- Which scope is allowed
- Which results count as valid
- When to stop
- When to ask the user
- When to move to the next phase

---

## 🏛 Architecture

### Symptom → Chat summary → Smash → Ship

<img src="assets/rkx-loop-flow1_3.png" alt="CURSORCERER RKX loop flow" width="900">

- Run artifacts are stored under `loops/<run>/`. Individual evidence packets are saved under: `loops/<run>/wave-N/slots/<slot-id>/attempts/<attempt-id>/report.md`

- The run artifacts preserve the investigation state and evidence trail, but they do not replace the required user-facing Chat summary.

---

## 🧱 Components

### 📂 What Ships

| Area | Public Form | Why It Exists |
| :--- | :--- | :--- |
| **Agents** | `agents/*.md` | Role contracts and responsibility boundaries |
| **Commands** | `commands/*.md` | Slash entry points for launching blueprints |
| **Rules** | `rules/*.mdc` | Workflow, loops, forensics, browser, and token policy |
| **Skills** | `skills/**/SKILL.md` | Phase and specialized workflows |
| **Hooks** | `hooks/*.py`, `*.sh` | Lifecycle escalation and human-readable summary |
| **Schemas** | `schemas/*.json`, `schemas/packets/` | Machine-readable protocol contracts |
| **Fixtures** | `scripts/fixtures/` | Verification scenarios |
| **Validators** | `scripts/` | Offline archive and runtime checks |
| **Reference** | `reference/` | Blueprint registry and telephony catalog |
| **Loops** | `loops/` | Run templates and decision surfaces |

### 🤖 Agent Crew

| Role | Responsibility |
| :--- | :--- |
| **`rkx-loop`** | Readonly dispatch and delivery |
| **`merger`** | Sole writer of shared run state |
| **`fact-slot`** | Checking one narrow evidence question |
| **`blueprint-scout`** | Finding reference patterns and coverage candidates |
| **`devil`** | Adversarial check of the leading root |
| **`implementer`** | L2 changes when implementation is authorized |
| **`boss`** | Checkpoint critic at waves 10 and 20 |

Agents are split by responsibility:

- The evidence agent does not make the final decision
- Merger does not write product code
- Advocate does not start a new wave on its own
- Implementer does not start edits unless implementation is authorized
- The Slack hook does not replace Chat summary

---

### 🔐 Public Boundary

The public archive contains the control-plane files and contracts. What stays local:
- Materialized runtime files
- Project-specific skills
- Local MCP overlays
- Run artifacts
- Runtime logs
- Install manifest
- Environment configuration
- Personal Cursor settings

The public version must not depend on one machine, one workspace, or one set of access rights.

---

## ⚡ Installation

The public archive is installed through Cursor Chat into one of two targets:

- **Project-local** — `<project>/.cursor` (scoped to that workspace)
- **User-global** — `~/.cursor` (shared across projects on this machine)

Pick the target before copying files. Do not mix the two without an explicit plan. 


<img src="assets/install-flow.png" alt="portable control-plane install flow" width="900">

The archive also includes the loop-flow diagram in `assets/`; these images are
part of the explicit public binary allowlist.

**Installation:**
1. Runs environment preflight
2. Checks capability availability
3. Compares target files
4. Shows conflicts
5. Creates a backup
6. Copies confirmed archive files as-is
7. Writes the install manifest
8. Runs validation

There is no need to assemble `.cursor` by hand, hunt for the right files, or guess the wiring order.

```bash
git clone <public-archive-url>
cd <archive-directory>
```

---

## ⚖️ License

MIT. See `LICENSE` and `NOTICE`.

---

## 👤 About the author

I'm Vladislav Rakhnianskii, solo founder of **RKX — Ad-to-Revenue OS for Meta Advertisers**.

RKX connects acquisition, measurement, sales, messaging, and AI workflows around Meta in one operating system.

I have been building the platform full-time since 2024, completely self-funded. We started charging two months ago and currently have:
- 5 paying customers
- $900 MRR
- $3,000+ collected
- 100% referral-driven growth
- Zero paid marketing

The product is already built and operational. I'm currently looking for a **strategic MarTech / SaaS angel investor** to help scale the company.

**Product:** 
https://rakhnianskii.com/

**Reach out:** 
https://wa.me/message/E26AP7ZUDRTLD1

**LinkedIn:** 
https://www.linkedin.com/in/rakhnianskii/