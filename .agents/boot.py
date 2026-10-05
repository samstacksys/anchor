#!/usr/bin/env python3
"""indie-mind boot manifest. READ-ONLY: prints what matters so the agent
reads only what the task needs. Run after compile_context.py, before work.

Usage:
    python3 .agents/boot.py
    python3 .agents/boot.py --json   # machine-readable manifest
"""
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

BASE = Path(__file__).resolve().parent
PLAN_FILE = BASE / "plan.md"
STATE_GRAPH = BASE / "architecture_state.json"
CURRENT_TASK_FILE = BASE / "current_task.md"
HISTORY_DIR = BASE / ".history"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def parse_plan() -> dict:
    """Extract project name + per-phase status list from plan.md."""
    text = read_text(PLAN_FILE)
    out = {"project": None, "phases": []}
    project = re.search(r'project_name:\s*["\']?([^"\'\n]+)', text)
    if project:
        out["project"] = project.group(1).strip()
    # Header: "### Phase N — Title" then "**Status:** X"
    for m in re.finditer(r"^###\s*Phase\s+(\d+[a-z]?)\s*[—-]\s*(.+)$", text, re.MULTILINE | re.IGNORECASE):
        number, title = m.group(1), m.group(2).strip()
        status = "UNKNOWN"
        status_match = re.search(
            rf"\*\*Status:\*\*\s*([A-Z_ \-]+(?:\d{{4}}-\d{{2}}-\d{{2}})?)", text[m.end():m.end() + 400]
        )
        if status_match:
            status = status_match.group(1).strip()
        out["phases"].append({"number": number, "title": title, "status": status})
    return out


def load_state() -> dict:
    try:
        data = json.loads(read_text(STATE_GRAPH))
        return {
            "decisions": data.get("decisions", []),
            "blockers": data.get("blockers", []),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"decisions": [], "blockers": []}


def load_target() -> str:
    text = read_text(CURRENT_TASK_FILE)
    # Tolerant header match: supports "## Active Targets" (new) and the old
    # emoji-prefixed templates, so old scratchpads still parse.
    m = re.search(r"##[^\n]*Active Targets(.*)", text, re.DOTALL)
    if not m:
        return ""
    # Drop template/instruction lines ("> ..."). Only real content counts.
    lines = [ln for ln in m.group(1).splitlines()
             if ln.strip() and not ln.strip().startswith(">")]
    return "\n".join(lines).strip()


def last_log() -> str:
    """Name of the most recent phase log, if any."""
    if not HISTORY_DIR.is_dir():
        return ""
    logs = sorted(
        HISTORY_DIR.glob("[0-9]*.md"), key=lambda p: p.name, reverse=True
    )
    return logs[0].name if logs else ""


def manifest() -> dict:
    plan = parse_plan()
    state = load_state()
    target = load_target()
    in_progress = [p for p in plan["phases"] if p["status"].startswith("IN_PROGRESS")]
    current = in_progress[-1] if in_progress else None
    if current is None:
        pending = [p for p in plan["phases"] if p["status"].startswith("NOT")]
        current = pending[0] if pending else None

    next_step = (
        "Holding: confirm the Active Target with the user before work."
        if not target
        else "Target set. Run compile_context.py --check, then start with a graphify query."
    )

    return {
        "project": plan["project"] or "(no plan.md frontmatter)",
        "current_phase": f"Phase {current['number']} — {current['title']}" if current else "none defined",
        "current_status": current["status"] if current else "—",
        "phases": plan["phases"],
        "decisions": state["decisions"],
        "blockers": state["blockers"],
        "active_target": target,
        "last_log": last_log(),
        "next_step": next_step,
    }


def render(manifest_dict: dict) -> str:
    d = manifest_dict
    lines = [
        "=" * 62,
        "indie-mind | boot manifest",
        f"   project : {d['project']}",
        f"   phase   : {d['current_phase']}",
        f"   status  : {d['current_status']}",
        "=" * 62,
        "",
        "Operating rules (always active):",
        "   1. ADHD output shape (i-have-adhd) — see AGENTS.md §2",
        "   2. Build + test gate before every commit",
        "   3. Graphify-first code browsing (code only, zero LLM cost)",
        "   4. One phase per session; IN_PROGRESS resumes exactly there",
        "",
    ]
    if d["decisions"]:
        lines.append("Immutable decisions:")
        for i, dec in enumerate(d["decisions"][:5], 1):
            lines.append(f"   {i}. {dec}")
        if len(d["decisions"]) > 5:
            lines.append(f"   … +{len(d['decisions']) - 5} more (see compile output)")
    else:
        lines.append("Immutable decisions: none recorded.")
    lines.append("")
    if d["blockers"]:
        lines.append("Active blockers:")
        for blk in d["blockers"][:5]:
            lines.append(f"   - [ ] {blk}")
    else:
        lines.append("Active blockers: none.")
    lines.append("")
    if d["active_target"]:
        lines.append(f"Active target:\n{d['active_target']}")
    else:
        lines.append("Active target: NOT SET.")
    lines.append("")
    if d["last_log"]:
        lines.append(f"Last phase log: {d['last_log']}")
    lines.append(f"Next: {d['next_step']}")
    lines.append("=" * 62)
    return "\n".join(lines)


if __name__ == "__main__":
    if "--json" in sys.argv:
        print(json.dumps(manifest(), indent=2))
    else:
        print(render(manifest()))