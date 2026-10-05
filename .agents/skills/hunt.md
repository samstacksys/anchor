---
description: "HUNT: reproduce, isolate, prove one hypothesis, fix with
  regression evidence, and re-run the original failure."
name: hunt
scope: project
version: 1.1.0
---

# HUNT → hunt

1.  Reproduce with one command or minimal input. If not reproducible,
    say so.
2.  Snapshot exact failure, input, command, environment facts that
    matter, and recent relevant changes.
3.  Locate the failing path and callers before editing.
4.  Form one falsifiable hypothesis and prove/disprove it with one
    targeted trace/read.
5.  Make the smallest fix and add regression evidence.
6.  Re-run the original failure, configured build/test gates, and
    relevant E2E.
7.  For network/data bugs, distinguish provider failure, rate limit,
    malformed input, parser drift, proxy failure, and application
    defect.
8.  Commit under the active phase.

After three failed hypotheses, stop and ask one diagnostic question
about the assumption most likely to be wrong.
