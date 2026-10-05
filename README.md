# Anchor

> Keep your AI coding agent grounded across every model, every session.

**A file-based state machine for human-in-the-loop AI development.**

Anchor doesn't give the agent more memory. **It gives it better memory.**

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/samstacksys/indie-mind/validate-hitl.yml?branch=main&label=CI)](https://github.com/samstacksys/indie-mind/actions)
[![Use this template](https://img.shields.io/badge/template-ready-2ea44f)](https://github.com/samstacksys/indie-mind/generate)

---

## The problem

You open a new session. The agent has no idea what you built yesterday.

So it does what agents do — it guesses. It invents functions that don't exist. It writes code that contradicts decisions you locked in three sessions ago. It starts touching files before you've confirmed what you even want it to do. And when something breaks, it re-diagnoses the same root cause six times without finding it, because nothing is grounded.

This isn't a model problem. It happens with GPT-4. It happens with Gemini. It happens with Claude. The model isn't broken — the workflow is.

Every session, your agent starts brain-dead. **Anchor fixes that.**

---

## What Anchor does

Anchor is a file-based state machine that lives in your repo. It gives every agent — Claude Code, Gemini CLI, openCode, GitHub Copilot — the same grounded starting point every session, regardless of which model is running underneath.

One compiled memory file. One confirmed target before any work begins. One trail that never gets lost.

**The agent reads decisions, not vibes.**

When a session ends, Anchor writes a phase log to `.agents/.history/`. When the next session starts, `compile_context.py` folds every log into a compressed state graph — locked decisions, active blockers, phase status. The agent reads that, not 40 files. `boot.py` prints exactly what matters. Nothing is reinvented.

When a phase is done, `plan.md` updates automatically. The next agent picks up exactly where the last one stopped.

---

## Works on free and cheap models

The sessions that built this were run on free OpenRouter models and openCode free tier.

Anchor is designed for builders on tight budgets. Instead of making every fresh agent session re-read the whole repository, old conversations, and every implementation detail, Anchor compiles the durable state and gives the agent **one active phase**.

The phase becomes the context boundary. The agent starts with the approved target, locked decisions, active blockers, product requirements, and the relevant roadmap slice. It then locates and reads only the code needed for that phase.

```text
entire project + previous sessions
              ↓
      compiled durable state
              ↓
        ONE active phase
              ↓
       relevant code only
              ↓
             work
              ↓
          phase log
              ↓
       next fresh session
```

That means fewer repeated repository reads, less irrelevant context, lower token usage, and less drift. Small context windows aren't a problem — they're the constraint Anchor was built around.

**Less context. Better context. Same project memory.**

Same workflow. Same discipline. Whatever model you can afford.

---

## The loop

Already have a PRD and roadmap? Start directly with `HANDOFF`.

```text
HANDOFF → compile durable state
             human confirms ONE phase/target
             target is written to current_task.md
             boot prints the session manifest
             handshake: will do / won't do / need from you

HAMMER  → implement only that approved target
             locate only relevant code
             build + test gate before every commit
             E2E / phase-specific evidence
             AUDIT before closeout
             commit + phase log

          → compile state again
          → open a fresh session
          → HANDOFF
          → repeat
```

Need to design a new project or rethink a major module first?

```text
GRILL → interrogate architecture → prd.md + plan.md → fresh session → HANDOFF
```

`GRILL` is optional. `HANDOFF` is the normal entry point for a project that is already planned.

Every session is lean. Every agent is grounded. Every decision survives.

---

## What survives between sessions

| File | What it holds |
|---|---|
| `.agents/project.yaml` | Project-specific build / test / E2E commands |
| `.agents/compile_context.py` | Compresses all history into one state graph |
| `.agents/current_task.md` | Active target + locked decisions (rewritten each session) |
| `.agents/plan.md` | Phase roadmap — status auto-updates on session close |
| `.agents/prd.md` | Product requirements — source of truth |
| `.agents/.history/phase-name.md` | Immutable phase log written at the end of every implementation session |
| `.agents/.history/index.md` | Generated chronological history index |
| `.agents/architecture_state.json` | Decision + blocker graph — append-only, never lost |
| `AGENTS.md` | Universal contract — auto-loads on every agent, every session |

---

## Supported agents

| Agent | How it loads |
|---|---|
| Claude Code | `CLAUDE.md` at repo root — auto-loaded |
| openCode | `AGENTS.md` at repo root — auto-loaded |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Gemini CLI | `AGENTS.md` — enable in settings |
| Aider / Codex / other | `AGENTS.md` is the universal contract |

One file governs all of them. The adapters are thin wrappers.

---

## Quick start

**One-time setup:**

```bash
git clone https://github.com/samstacksys/anchor my-project
cd my-project
pip install pyyaml
python .agents/compile_context.py
python .agents/boot.py
```

**Normal loop:**

```text
type HANDOFF  →  start or resume one phase
type HAMMER   →  implement the approved target
type AUDIT    →  verify before closing
type HUNT     →  debug a reproducible failure
type STARTER  →  normal questions / micro-work
type GRILL    →  optional architecture interrogation
```

---

## Project structure

```
├── AGENTS.md                    ← universal agent contract (all agents)
├── CLAUDE.md                    ← thin Claude Code bridge
├── GITHUB_GUIDE.md              ← issue / branch / PR workflow
└── .agents/
    ├── project.yaml             ← project-specific build / test / E2E commands
    ├── compile_context.py       ← state machine — single source of memory
    ├── boot.py                  ← manifest printer — run first each session
    ├── prd.md                   ← product requirements
    ├── plan.md                  ← phase roadmap
    ├── current_task.md          ← active target + inherited decisions
    ├── architecture_state.json  ← decision graph (compile only)
    ├── templates/               ← canonical phase-log template
    ├── .history/                ← phase logs + generated index
    └── skills/                  ← trigger-word playbooks
```

---

## Context boundaries and roadmap safety

Anchor treats a phase as a deliberate context boundary, not just a checklist item. Keep phases small enough to fit comfortably inside the configured context budget. If a phase runs long, write an `IN_PROGRESS` log and resume it through a fresh `HANDOFF` instead of dragging a bloated session forward.

`plan.md` carries a `roadmap_id`, and phase logs record the roadmap they belong to. If a roadmap is materially renumbered later, old phase logs remain historical evidence without accidentally completing a new phase that happens to reuse the same number.

Project commands are stack-independent and live in `.agents/project.yaml`. Anchor does not assume npm, Python, Rust, Go, or any particular build system.

---

## Credits

Two vendored skills:

- [graphify](https://github.com/Graphify-Labs/graphify) · Apache-2.0 — code-graph navigation, local AST, zero API cost
- [i-have-adhd](https://github.com/ayghri/i-have-adhd) · MIT — the 10 output-shape rules in `AGENTS.md`

---

## License

MIT © [samstacksys](LICENSE). Third-party components carry their own licenses — see [NOTICE](NOTICE).
