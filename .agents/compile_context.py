#!/usr/bin/env python3
"""indie-mind state machine — single source of cross-phase memory.

Every state file lives inside .agents/ (canonical home). BASE is resolved
from the script location, not CWD, so `python3 .agents/compile_context.py`
works no matter where it is invoked from.

Modes:
    (no args)         Normal: sync state, flip prd.md COMPLETED for COMPLETE
                      logs, rewrite current_task.md, read-only on .history/.
    --check           Read-only CI mode: validate the state machine without
                      writing. Exits 0 if healthy, 1 on hard errors.
"""
import os
import re
import sys
import json
import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parent

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass
HISTORY_DIR = BASE / ".history"
INDEX_FILE = HISTORY_DIR / "index.md"
CURRENT_TASK_FILE = BASE / "current_task.md"
STATE_GRAPH = BASE / "architecture_state.json"
PRD_FILE = BASE / "prd.md"
PLAN_FILE = BASE / "plan.md"

REQUIRED_FRONTMATTER = ("date", "phase", "status")
VALID_STATUSES = ("COMPLETE", "IN_PROGRESS")

# ── WHICH ROADMAP IS A PHASE NUMBER BELONGING TO? ─────────────────────────────
# `phase: Phase 7` on its own is NOT an identity. plan.md was renumbered on
# 2026-09-29 (Phase 9 was reassigned to AR Cámara, the dashboard guard became
# 9b, Payment Chasing became Phase 7), and the .history/ logs were numbered
# independently of it. So the same number names two different pieces of work:
#
#     .history/phase-7.md   "Phase 7" = the SUPER ADMIN PANEL  (old numbering)
#     2026-09-29-phase-7-cobros.md  "Phase 7" = PAYMENT CHASING (new numbering)
#
# Matching the number with a PREFIX regex made a COMPLETE log for the Super Admin
# panel flip the new Phase 7 to "COMPLETED (2026-09-26)" — work that had never
# been started. It was reverted three times across three sessions, and every
# session re-learned it from scratch.
#
# So a log now says which roadmap it belongs to, and only logs from the CURRENT
# roadmap may stamp plan.md. A log that does not declare one is treated as the
# legacy generation (r1) rather than guessed at: not knowing is a reason to
# abstain, never a reason to assume.
#
# TO BUMP: when plan.md is renumbered again, add a new generation id here and
# tag the logs written under it with that id. Old logs keep their own.
def current_roadmap():
    """Read roadmap_id from plan.md frontmatter. Fresh projects default to r1."""
    try:
        text = PLAN_FILE.read_text(encoding="utf-8")
    except OSError:
        return "r1"
    m = re.search(r'^roadmap_id:\s*["\']?([^"\'\n]+)', text, re.MULTILINE)
    return m.group(1).strip() if m else "r1"


ROADMAP = current_roadmap()
LEGACY_ROADMAP = "r1"


def phase_number(phase):
    """The digits in a `phase:` value, or None.

    ONE definition. This was previously three copies of the same regex, which is
    how they drifted apart in the first place.

    A descriptive suffix is TOLERATED on purpose — "Phase 2 — Facturae Móvil UI"
    is a real Phase 2 with a title, and refusing to count it would silently stop
    a finished phase from ever being stamped. The old note here blamed the prefix
    match for the plan.md corruption; it was not the real cause. The real cause
    was that a NUMBER alone was treated as an identity across two different
    roadmaps, and that is what `roadmap:` fixes. Making this regex stricter would
    have hidden the bug behind a second one.

    A suffix LETTER is kept, so 9b (the dashboard guard) stays distinct from 9
    (AR Cámara) rather than being folded into it."""
    m = re.match(r"^\s*Phase\s+(\d+[a-z]?)\b", str(phase or ""), re.IGNORECASE)
    return m.group(1).lower() if m else None


def roadmap_of(meta):
    """The roadmap generation a log belongs to. Untagged = the legacy one."""
    tag = str((meta or {}).get("roadmap") or "").strip().lower()
    return tag or LEGACY_ROADMAP


def in_current_roadmap(meta):
    return roadmap_of(meta) == ROADMAP



def init_environment():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)
    if not os.path.exists(STATE_GRAPH):
        with open(STATE_GRAPH, 'w') as f:
            json.dump({"decisions": [], "blockers": []}, f)


def read_logs():
    """Parse every .history/*.md log (except index.md).

    Returns a list of dicts: filename, meta (dict or None), errors (list),
    raw content. Logs with unreadable YAML are kept with an error entry so
    --check can report them and normal mode can warn instead of silently
    dropping the phase's decisions.
    """
    logs = []
    if not HISTORY_DIR.is_dir():
        return logs
    for filename in sorted(os.listdir(HISTORY_DIR)):
        if not filename.endswith(".md") or filename == "index.md":
            continue
        filepath = HISTORY_DIR / filename
        try:
            content = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            logs.append({"filename": filename, "meta": None,
                         "errors": ["unreadable file"], "content": ""})
            continue
        if content.startswith("\ufeff"):  # Windows UTF-8 BOM
            content = content[1:]
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not match:
            logs.append({"filename": filename, "meta": None,
                         "errors": ["missing YAML frontmatter"], "content": content})
            continue
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as exc:
            logs.append({"filename": filename, "meta": None,
                         "errors": [f"invalid YAML: {exc}"], "content": content})
            continue
        errors = [k for k in REQUIRED_FRONTMATTER if k not in meta]
        if meta.get("status") not in VALID_STATUSES:
            errors.append(f"status must be one of {VALID_STATUSES}")
        logs.append({"filename": filename, "meta": meta,
                     "errors": errors, "content": content})
    return logs


def iter_completed_phases():
    """Phase numbers (as strings) that have a COMPLETE log **in the current
    roadmap**. IN_PROGRESS logs are NOT counted — their phase stays
    PENDING/IN_PROGRESS so the next session resumes it.

    Logs from an earlier roadmap generation are excluded even when they are
    COMPLETE. See the ROADMAP note above: that exclusion is the whole fix."""
    numbers = set()
    for log in read_logs():
        meta = log["meta"]
        if not meta or log["errors"]:
            continue
        if not in_current_roadmap(meta):
            continue
        num = phase_number(meta.get("phase"))
        if num and meta.get("status") == "COMPLETE":
            numbers.add(num)
    return sorted(numbers)


def completed_log_dates():
    """phase number -> latest COMPLETE log date, current roadmap only."""
    dates = {}
    for log in read_logs():
        meta = log["meta"]
        if not meta or log["errors"]:
            continue
        if not in_current_roadmap(meta):
            continue
        num = phase_number(meta.get("phase"))
        if num and meta.get("status") == "COMPLETE" and meta.get("date"):
            day = str(meta["date"])
            if day > dates.get(num, "0000-00-00"):
                dates[num] = day
    return dates


def roadmap_collisions():
    """Phase numbers that name DIFFERENT work in different roadmap generations.

    This is the diagnostic that should have caught the problem the first time it
    cost somebody a session: the same digits, two meanings.

    Returns (collisions, untagged) where `collisions` maps a phase number to the
    roadmap generations seen for it (only where there is more than one) and
    `untagged` lists the files in a colliding group that carry NO `roadmap:` field
    at all. An untagged file in a colliding group is the trap still half-open: it
    is read as the legacy roadmap, and if it is COMPLETE it can still flip
    plan.md. Every log in a colliding group must be tagged explicitly."""
    grouped = {}
    for log in read_logs():
        meta = log["meta"]
        if not meta or log["errors"]:
            continue
        num = phase_number(meta.get("phase"))
        if not num:
            continue
        grouped.setdefault(num, []).append(log)

    collisions = {}
    untagged = []
    for num, logs in sorted(grouped.items()):
        generations = {roadmap_of(l["meta"]) for l in logs}
        if len(generations) < 2:
            continue
        collisions[num] = sorted(generations)
        loose = sorted(
            l["filename"] for l in logs
            if not str((l["meta"] or {}).get("roadmap") or "").strip()
        )
        if loose:
            untagged.append(f"Phase {num}: {', '.join(loose)}")
    return collisions, untagged


def sync_phase_statuses():
    """Flip `**Status:** NOT STARTED`/`PENDING` -> `COMPLETED (date)` in BOTH
    plan.md and prd.md, but ONLY for phases with a COMPLETE log. This is what
    boot.py reads to pick the current phase; keeping plan.md stale here is what
    broke the loop (boot showed Phase 5 while Phase 8 was done). Idempotent."""
    completed = iter_completed_phases()
    if not completed:
        return
    dates = completed_log_dates()

    for target in (PLAN_FILE, PRD_FILE):
        if not target.exists():
            continue
        with open(target, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_phase = None
        changed = False
        for i, line in enumerate(lines):
            header = re.match(r'^#{2,3}\s*Phase\s+(\d+)', line)
            if header:
                current_phase = header.group(1)
            elif current_phase in completed:
                m = re.match(r'^-?\s*\*\*Status:\*\*\s*`?(NOT STARTED|PENDING)`?(\s|$)', line)
                if m:
                    stamp = f"COMPLETED ({dates.get(current_phase)})" if dates.get(current_phase) else "COMPLETED"
                    lines[i] = re.sub(r'`?(NOT STARTED|PENDING)`?', stamp, line, count=1)
                    changed = True

        if changed:
            with open(target, 'w', encoding='utf-8') as f:
                f.writelines(lines)


def sync_state_from_logs():
    """Merge decisions + blockers from every log into architecture_state.json
    and rebuild .history/index.md. Logs are archived, never deleted."""
    init_environment()
    decisions = []
    blockers = []
    log_entries = []

    for log in read_logs():
        meta = log["meta"]
        if not meta or log["errors"]:
            continue
        date = meta.get('date', 'Unknown')
        phase = meta.get('phase', 'N/A')
        status = meta.get('status', 'N/A')

        if meta.get('decisions'):
            decisions.extend(f"{d} ({date})" for d in meta['decisions'])
        if meta.get('blockers'):
            blockers.extend(f"{b} (Phase: {phase})" for b in meta['blockers'])

        flag = " <in-progress>" if status == "IN_PROGRESS" else ""
        log_entries.append(
            f"| {date} | {phase}{flag} | `{status}` | [{log['filename']}]({log['filename']}) |"
        )

    with open(STATE_GRAPH, 'w', encoding='utf-8') as f:
        json.dump({"decisions": sorted(set(decisions)), "blockers": blockers},
                  f, indent=2)

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write("# Historic Chronological Index\n\n"
                "| Date | Phase | Status | File |\n| :--- | :--- | :--- | :--- |\n")
        f.write("\n".join(log_entries))


def existing_active_targets():
    """Whatever is currently under `## Active Targets`, verbatim, or "".

    THE SESSION TARGET IS WRITTEN BY HAND, AFTER compile runs, and this function
    used to overwrite it with a placeholder on every single invocation. The
    ritual depends on that order — compile first, then the agent writes the
    target — which meant the target was destroyed by any LATER compile, including
    the one at the end of the session when the phase log is closed.

    So the section is PRESERVED, not regenerated. Two reasons that is the right
    default rather than a convenience: the placeholder is indistinguishable from a
    real target unless you read the prose, and the whole point of the section is
    that the next session inherits a human's decision rather than a default. Only
    the two generated sections above it are owned by this script."""
    if not CURRENT_TASK_FILE.exists():
        return ""
    try:
        content = CURRENT_TASK_FILE.read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"^##\s+Active Targets\s*$(.*)\Z", content, re.MULTILINE | re.DOTALL)
    if not m:
        return ""
    body = m.group(1).strip()
    # The untouched placeholder is not a target. Dropping it keeps the section
    # from looking populated to the next agent.
    if not body or body.startswith("> [AGENT:"):
        return ""
    return body


def generate_active_workspace():
    with open(STATE_GRAPH, 'r', encoding='utf-8') as f:
        state = json.load(f)

    targets = existing_active_targets()

    with open(CURRENT_TASK_FILE, 'w', encoding='utf-8') as f:
        f.write("# ACTIVE MICRO-TASK SCRATCHPAD\n\n")
        f.write("## Immutable Architectural Decisions\n")
        if state["decisions"]:
            for dec in state["decisions"]:
                f.write(f"- {dec}\n")
        else:
            f.write("- No structural constraints recorded.\n")

        f.write("\n## Active System Blockers\n")
        if state["blockers"]:
            for blk in state["blockers"]:
                f.write(f"- [ ] {blk}\n")
        else:
            f.write("- No active blockers. Slate is clean.\n")

        f.write("\n## Active Targets\n")
        if targets:
            f.write(targets + "\n")
        else:
            f.write("> [AGENT: write the session target here after confirming it with the user]\n")


def check_only():
    """Read-only CI validation. Returns exit code: 0 healthy, 1 hard errors."""
    problems = []
    warnings = []
    logs = read_logs()

    if not HISTORY_DIR.is_dir():
        warnings.append(".history/ does not exist yet")

    if not logs:
        warnings.append("no phase logs found (fresh project?)")

    seen_phases = []
    in_progress = []
    for log in logs:
        if log["errors"]:
            problems.append(f"{log['filename']}: {', '.join(log['errors'])}")
            continue
        meta = log["meta"]
        seen_phases.append(meta["phase"])
        if meta["status"] == "IN_PROGRESS":
            in_progress.append(log["filename"])

    # Phase order: numbers should be non-decreasing in time.
    numbers = []
    for ph in seen_phases:
        num = phase_number(ph)
        if num:
            numbers.append(int(re.match(r"\d+", num).group(0)))
    if numbers != sorted(numbers):
        warnings.append(f"out-of-order phase logs: {numbers}")

    for prd in (CURRENT_TASK_FILE, STATE_GRAPH):
        if not prd.exists():
            warnings.append(f"{prd.name} missing (run once without --check)")

    # The collision diagnostic. Collisions themselves are EXPECTED — plan.md was
    # renumbered and the logs were not, which is why the `roadmap:` field exists.
    # What is not acceptable is a colliding group with an untagged file in it, so
    # that one is a warning and the bare fact of a collision is only printed.
    collisions, untagged = roadmap_collisions()
    if collisions:
        print(f"  roadmap:      {ROADMAP} (only this generation may stamp plan.md)")
        for num, generations in collisions.items():
            print(f"  NOTE Phase {num} spans generations {'/'.join(generations)} — logs are tagged, so this is safe")
    for u in untagged:
        warnings.append(f"colliding phase group has an UNTAGGED log — {u}")

    try:
        with open(STATE_GRAPH, 'r', encoding='utf-8') as f:
            json.load(f)
    except (OSError, json.JSONDecodeError):
        problems.append(f"{STATE_GRAPH.name} is not valid JSON")

    print("indie-mind state check")
    print(f"  logs:         {len(logs)}")
    print(f"  in progress:  {', '.join(in_progress) if in_progress else 'none'}")
    print(f"  phases seen:  {seen_phases if seen_phases else 'none'}")
    for w in warnings:
        print(f"  WARN {w}")
    for p in problems:
        print(f"  ERROR {p}")
    if not problems:
        print("  state machine: OK")
    return 1 if problems else 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check_only())

    # Normal mode — warn on unreadable logs but keep going.
    for log in read_logs():
        if log["errors"]:
            print(f"Skipping {log['filename']}: {', '.join(log['errors'])}")

    # Same diagnostic as --check, in write mode, and it says out loud which
    # generation is allowed to touch plan.md. Three sessions each ran compile,
    # saw plan.md rewrite itself, and reverted it by hand; this is the line that
    # makes the rewrite impossible to mistake for progress.
    collisions, untagged = roadmap_collisions()
    print(f"Roadmap generation in force: {ROADMAP} (only its logs can stamp plan.md)")
    if collisions:
        for num, generations in collisions.items():
            print(f"  NOTE  Phase {num} spans generations {'/'.join(generations)} — tagged, so it is safe")
    for u in untagged:
        print(f"  WARN  colliding phase group has an UNTAGGED log — {u}")

    print("Processing context memory optimization...")
    sync_state_from_logs()
    sync_phase_statuses()
    generate_active_workspace()
    print("Done! current_task.md and the phase statuses in plan.md/prd.md are up to date.")
    print("    Next: python3 .agents/boot.py — or --check for read-only CI mode.")