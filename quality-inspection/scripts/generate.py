#!/usr/bin/env python3
"""
Phase 3: Report generation for Quality Inspection.
Generates inspection_report.json and inspection_report.md from judged_data.json.
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
TEMPLATE_FILE = "inspection_report.md.j2"


def format_spec(spec_min, spec_max, unit):
    """Format spec range for display."""
    if spec_min is not None and spec_max is not None:
        return f"{spec_min}~{spec_max}{unit}"
    elif spec_max is not None:
        return f"~{spec_max}{unit}"
    elif spec_min is not None:
        return f"{spec_min}~{unit}"
    return "-"


def result_icon(final_result):
    """Return icon for judgment result."""
    return {
        "PASS": "✅",
        "CONDITIONAL PASS": "⚠️✅",
        "FAIL": "❌",
    }.get(final_result, "?")


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
    env.globals["format_spec"] = format_spec
    env.globals["result_icon"] = result_icon

    return env.get_template(TEMPLATE_FILE)


# =============================================================================
# Statistics
# =============================================================================

def compute_statistics(data: dict) -> dict:
    """Compute summary statistics from judged data."""
    results = data.get("results", [])

    by_result = Counter(r.get("final_result", "unknown") for r in results)
    by_category = Counter(r.get("category", "unknown") for r in results)
    by_defect = Counter(
        r["defect_code"] for r in results if r.get("defect_code")
    )
    by_priority = Counter(
        r["priority"] for r in results if r.get("priority")
    )

    total = len(results)
    pass_count = by_result.get("PASS", 0) + by_result.get("CONDITIONAL PASS", 0)
    pass_rate = (pass_count / total * 100) if total > 0 else 0

    return {
        "total_measurements": total,
        "pass_count": by_result.get("PASS", 0),
        "conditional_pass_count": by_result.get("CONDITIONAL PASS", 0),
        "fail_count": by_result.get("FAIL", 0),
        "pass_rate_pct": round(pass_rate, 1),
        "by_category": dict(by_category),
        "by_defect_code": dict(by_defect),
        "by_priority": dict(by_priority),
    }


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Quality Inspection - Report Generation (Phase 3)"
    )
    parser.add_argument(
        "--judged-data",
        required=True,
        help="LLM 판단 완료 데이터 (judged_data.json)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        required=True,
        help="출력 디렉토리",
    )
    args = parser.parse_args()

    judged_path = Path(args.judged_data).resolve()
    if not judged_path.exists():
        print(f"[ERROR] File not found: {judged_path}")
        sys.exit(1)

    with open(judged_path, encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n=== Report Generation ===\n")

    # Compute statistics
    stats = compute_statistics(data)
    print(f"  Total: {stats['total_measurements']}")
    print(f"  Pass: {stats['pass_count']} | Conditional: {stats['conditional_pass_count']} | Fail: {stats['fail_count']}")
    print(f"  Rate: {stats['pass_rate_pct']}%")

    # Build report JSON
    report = {
        "meta": {
            **data.get("meta", {}),
            "generated_at": datetime.now().isoformat(),
        },
        "results": data.get("results", []),
        "system_issues": data.get("system_issues", []),
        "summary": data.get("summary", {}),
        "statistics": stats,
    }

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = output_dir / "inspection_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  [OK] JSON: {json_path}")

    # Render Markdown from template
    template = load_template()
    print(f"  [TMPL] Loaded: {TEMPLATE_DIR / TEMPLATE_FILE}")

    md_content = template.render(
        meta=data.get("meta", {}),
        summary=data.get("summary", {}),
        results=data.get("results", []),
        system_issues=data.get("system_issues", []),
        statistics=stats,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    md_path = output_dir / "inspection_report.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"  [OK] Markdown: {md_path}")

    print(f"\n[OK] Report generation complete: {output_dir}")


if __name__ == "__main__":
    main()
