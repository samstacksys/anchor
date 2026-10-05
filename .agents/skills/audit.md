---
description: "AUDIT: phase closeout gate for scope, contracts, tests,
  evidence, secrets, state-machine health, and log integrity."
name: audit
scope: project
version: 1.1.0
---

# AUDIT → audit

Verdict first: PASS or FAIL.

Check: 1. Scope: every diff belongs to the active target; no hidden
refactor. 2. Contracts: callers/consumers updated; migrations/backward
compatibility handled where applicable. 3. Verification: configured
build/test/E2E are green; phase-specific benchmark or data-quality gates
are green. 4. Safety: no secrets; destructive/data-loss behavior
reviewed; external/AI data treated as untrusted; provenance/cost/failure
telemetry present when required. 5. State: `compile_context.py --check`
exits 0; phase log has date, roadmap, phase, status, decisions,
blockers, files changed, verification, and next state.

On FAIL, list at most five ranked blockers and return to HUNT/HAMMER. On
PASS, close the phase.
