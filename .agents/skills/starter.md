---
description: "HANDOFF ritual: compile → human target → current_task →
  boot → handshake → approved work."
name: starter
scope: project
version: 1.1.0
---

# HANDOFF → starter

Trigger only when the user types `HANDOFF`.

1.  Run `python3 .agents/compile_context.py`.
2.  Read only the next relevant phase in `.agents/plan.md`.
3.  Ask one question: confirm that phase, or ask for the session target.
4.  Write the answer under `## Active Targets` in
    `.agents/current_task.md`. Include deliverable and out-of-scope.
5.  Run `python3 .agents/boot.py`. If target is unset, fix step 4.
6.  Give exactly three handshake lines: will do / will not do / need
    from user.
7.  On approval, use HAMMER.

If an `IN_PROGRESS` log exists for the active phase, resume it. Do not
re-plan or mark it complete.

A fresh session without `HANDOFF` is normal mode, not this skill.
