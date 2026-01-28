#!/usr/bin/env python3
"""
Phase 3: Report generation for Meeting Minutes Processor.
Generates action_report.json and action_report.md from judged_data.json.
Uses Jinja2 template from templates/ folder for Markdown output.
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


# =============================================================================
# Template Helpers
# =============================================================================

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
TEMPLATE_FILE = "action_report.md.j2"


def priority_icon(priority):
    """Return icon for priority level."""
    return {
        "high": "🔴 High",
        "medium": "🟡 Medium",
        "low": "🟢 Low",
    }.get(priority, priority or "-")


def load_template():
    """Load Jinja2 template from templates/ directory."""
    if not TEMPLATE_DIR.exists():
        print(f"[ERROR] Templates directory not found: {TEMPLATE_DIR}")
        sys.exit(1)

    template_path = TEMPLATE_DIR / TEMPLATE_FILE
    if not template_path.exists():
        print(f"[ERROR] Template file not found: {template_path}")
        sys.exit(1)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["priority_icon"] = priority_icon

    return env.get_template(TEMPLATE_FILE)


# =============================================================================
# Statistics
# =============================================================================

def compute_statistics(data: dict) -> dict:
    """Compute summary statistics from judged data."""
    actions = data.get("action_items", [])

    by_priority = Counter(a.get("priority", "unknown") for a in actions)
    by_category = Counter(a.get("category", "unknown") for a in actions)
    by_owner = Counter(a.get("owner", "unassigned") for a in actions)
    by_source = Counter(a.get("source", "unknown") for a in actions)

    return {
        "total_actions": len(actions),
        "by_priority": dict(by_priority),
        "by_category": dict(by_category),
        "by_owner": dict(by_owner),
        "explicit_count": by_source.get("explicit", 0),
        "implicit_count": by_source.get("implicit", 0),
        "total_decisions": len(data.get("decisions", [])),
        "total_unresolved": len(data.get("unresolved", [])),
    }


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Meeting Minutes Processor - Report Generation (Phase 3)"
    )
    parser.add_argument(
        "--judged-data",
        required=True,
        help="LLM 판단 완료 데이터 (judged_data.json)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        required=True,
        help="출력 디렉토리 (action_report.json + .md)",
    )
    args = parser.parse_args()

    # Load judged data
    judged_path = Path(args.judged_data).resolve()
    if not judged_path.exists():
        print(f"[ERROR] File not found: {judged_path}")
        sys.exit(1)

    with open(judged_path, encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n=== Report Generation ===\n")

    # Compute statistics
    stats = compute_statistics(data)
    print(f"  - Total actions: {stats['total_actions']}")
    print(f"  - Decisions: {stats['total_decisions']}")
    print(f"  - Unresolved: {stats['total_unresolved']}")

    # Build final report JSON
    report = {
        "meta": {
            **data.get("meta", {}),
            "generated_at": datetime.now().isoformat(),
        },
        "summary": data.get("summary", ""),
        "decisions": data.get("decisions", []),
        "action_items": data.get("action_items", []),
        "unresolved": data.get("unresolved", []),
        "tracker_updates": data.get("tracker_updates", []),
        "statistics": stats,
    }

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = output_dir / "action_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  [OK] JSON: {json_path}")

    # Render Markdown from template
    template = load_template()
    print(f"  [TMPL] Loaded: {TEMPLATE_DIR / TEMPLATE_FILE}")

    md_content = template.render(
        meta=data.get("meta", {}),
        summary=data.get("summary", ""),
        decisions=data.get("decisions", []),
        action_items=data.get("action_items", []),
        unresolved=data.get("unresolved", []),
        tracker_updates=data.get("tracker_updates", []),
        statistics=stats,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    md_path = output_dir / "action_report.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"  [OK] Markdown: {md_path}")

    print(f"\n[OK] Report generation complete: {output_dir}")


if __name__ == "__main__":
    main()
