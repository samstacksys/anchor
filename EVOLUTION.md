# Evolution Guide

## Changes in this Anchor v1.1

### 1. Stack assumptions moved out of the contract

Old versions embedded commands such as `npm run build`. The framework
now uses `.agents/project.yaml`, so Python, Node, Rust, Go, mixed
stacks, and non-code projects can share the same workflow.

### 2. GRILL is optional

A project with an already approved PRD/roadmap can begin directly with
HANDOFF. GRILL remains useful for uncertain architecture or major
redesigns.

### 3. Roadmap identity is project data

`compile_context.py` now reads `roadmap_id` from `plan.md` instead of
carrying a project-specific hard-coded roadmap generation. Phase
suffixes such as `9b` are preserved by both compiler and boot parser.

### 4. Tooling is capability-based

Graphify is no longer assumed to exist. Projects may add a Graphify
skill, but the base workflow falls back to targeted repository
search/read.

### 5. Phase evidence is broader than unit tests

The universal contract distinguishes build/test/E2E from phase-specific
evidence such as crawler benchmarks, AI evaluation sets, migration
checks, cost measurements, and data-quality tests.

## Migrating an existing project

1.  Add `.agents/project.yaml` and move project commands there.
2.  Add `roadmap_id` to `plan.md`.
3.  Ensure new phase logs include `roadmap: <roadmap_id>`.
4.  Replace the old generic skills with the v1.1 skills, keeping any
    project-specific compliance skills separately.
5.  Run `python3 .agents/compile_context.py --check` before allowing the
    compiler to write.

Do not rewrite old phase logs merely for aesthetics. History is
evidence. Add compatibility only when the compiler requires it.
