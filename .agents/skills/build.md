---
description: "HAMMER: implement exactly the approved active target with
  configured gates, evidence, audit, commit, and phase log."
name: build
scope: project
version: 1.1.0
---

# HAMMER → build

Trigger on `HAMMER` or after an approved HANDOFF handshake.

1.  Read `.agents/current_task.md`, the matching plan section, and
    `.agents/project.yaml`. State scope/out-of-scope in two lines.
2.  Locate before editing. Use the repo's configured navigation method;
    read exact code and callers.
3.  Implement one bounded change at a time. No unrelated cleanup.
4.  Run configured build + test before every commit. Do not invent
    missing commands.
5.  Before phase close, run configured E2E. For data/AI/crawler phases,
    also run the phase's benchmark/cost/provenance checks.
6.  Run AUDIT. FAIL means fix first.
7.  Commit with `phase-N: <result>`.
8.  Write `.agents/.history/YYYY-MM-DD-phase-N.md` from the template
    with roadmap, status, decisions, blockers, files, verification, and
    next state.
9.  Run compile, then compile `--check`.

One phase per session. If context/time runs out, log `IN_PROGRESS`,
commit the safe state, compile, and stop.
