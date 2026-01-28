#!/usr/bin/env python3
"""
Phase 1-2: Data extraction for Meeting Minutes Processor.
Extracts attendees, action items, decisions, dates from converted meeting notes.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml


# =============================================================================
# Configuration
# =============================================================================

def load_config() -> dict:
    """Load settings.yaml configuration."""
    config_paths = [
        Path(__file__).parent.parent / "config" / "settings.yaml",
        Path("config") / "settings.yaml",
    ]
    for config_path in config_paths:
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    print("[WARN] settings.yaml not found, using defaults")
    return {}


# =============================================================================
# Extraction Functions
# =============================================================================

def extract_attendees(lines: list[str], config: dict) -> list[str]:
    """Extract attendee names from meeting notes."""
    keywords = config.get("attendees", {}).get("keywords", ["참석:", "Attendees:"])
    attendees = []

    for i, line in enumerate(lines):
        for kw in keywords:
            if kw in line:
                # Extract names after the keyword
                after = line.split(kw, 1)[1].strip()
                # Split by common delimiters
                names = re.split(r"[,、/·]", after)
                attendees.extend(n.strip() for n in names if n.strip())
                # Check continuation lines (indented or comma-separated)
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith("-") or next_line.startswith("•"):
                        attendees.append(next_line.lstrip("-•").strip())
                    elif not next_line:
                        break
                break
    return attendees


def extract_explicit_actions(lines: list[str], config: dict) -> list[dict]:
    """Extract explicitly marked action items."""
    keywords = config.get("action_items", {}).get("keywords", ["할 일:", "TODO:"])
    actions = []

    for i, line in enumerate(lines):
        for kw in keywords:
            if kw in line:
                actions.append({
                    "line_number": i + 1,
                    "matched_keyword": kw,
                    "text": line.strip(),
                })
                break
    return actions


def extract_decisions(lines: list[str], config: dict) -> list[dict]:
    """Extract decision items."""
    keywords = config.get("decisions", {}).get("keywords", ["결정:", "Decided:"])
    decisions = []

    for i, line in enumerate(lines):
        for kw in keywords:
            if kw in line:
                decisions.append({
                    "line_number": i + 1,
                    "matched_keyword": kw,
                    "text": line.strip(),
                })
                break
    return decisions


def extract_dates(lines: list[str], config: dict) -> list[dict]:
    """Extract date references."""
    patterns = config.get("date_patterns", [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{1,2}/\d{1,2}",
        r"\d{1,2}월\s*\d{1,2}일",
    ])
    dates = []

    for i, line in enumerate(lines):
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for m in matches:
                dates.append({
                    "line_number": i + 1,
                    "date_text": m,
                })
    return dates


def extract_tracker_refs(lines: list[str], config: dict) -> list[dict]:
    """Extract references to existing tracker IDs."""
    pattern = config.get("tracker_id_pattern", r"[A-Z]+-\d+")
    refs = []

    for i, line in enumerate(lines):
        matches = re.findall(pattern, line)
        for m in matches:
            refs.append({
                "line_number": i + 1,
                "tracker_id": m,
                "context": line.strip(),
            })
    return refs


def extract_sections(lines: list[str], config: dict) -> list[dict]:
    """Extract document sections by headers."""
    header_patterns = config.get("section_headers", [
        r"^#{1,3}\s+",
        r"^\d+\.\s+",
        r"^【.+】",
        r"^\[.+\]",
    ])
    sections = []
    current = None

    for i, line in enumerate(lines):
        is_header = False
        for pattern in header_patterns:
            if re.match(pattern, line.strip()):
                is_header = True
                break

        if is_header:
            if current:
                current["content"] = "\n".join(
                    lines[current["start_line"] - 1 : i]
                ).strip()
                sections.append(current)
            current = {
                "header": line.strip(),
                "start_line": i + 1,
                "content": "",
            }

    # Last section
    if current:
        current["content"] = "\n".join(
            lines[current["start_line"] - 1 :]
        ).strip()
        sections.append(current)

    return sections


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Meeting Minutes Processor - Data Extraction (Phase 1-2)"
    )
    parser.add_argument(
        "--converted",
        required=True,
        help="변환된 회의록 파일 경로 (meeting_notes.md)",
    )
    parser.add_argument(
        "--tracker",
        help="기존 프로젝트 트래커 JSON 경로 (선택)",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="출력 JSON 파일 경로 (raw_data.json)",
    )
    args = parser.parse_args()

    # Load config
    config = load_config()

    # Read converted file
    converted_path = Path(args.converted).resolve()
    if not converted_path.exists():
        print(f"[ERROR] File not found: {converted_path}")
        sys.exit(1)

    content = converted_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    print(f"\n=== Data Extraction: {converted_path.name} ===\n")

    # Extract data
    attendees = extract_attendees(lines, config)
    print(f"  - attendees: {len(attendees)} found")

    explicit_actions = extract_explicit_actions(lines, config)
    print(f"  - explicit actions: {len(explicit_actions)} found")

    decisions = extract_decisions(lines, config)
    print(f"  - decisions: {len(decisions)} found")

    dates = extract_dates(lines, config)
    print(f"  - dates: {len(dates)} found")

    tracker_refs = extract_tracker_refs(lines, config)
    print(f"  - tracker refs: {len(tracker_refs)} found")

    sections = extract_sections(lines, config)
    print(f"  - sections: {len(sections)} found")

    # Load existing tracker if provided
    tracker_data = None
    if args.tracker:
        tracker_path = Path(args.tracker).resolve()
        if tracker_path.exists():
            with open(tracker_path, encoding="utf-8") as f:
                tracker_data = json.load(f)
            print(f"  - tracker loaded: {len(tracker_data.get('items', []))} items")

    # Build output
    output = {
        "meta": {
            "source_file": str(converted_path),
            "extraction_timestamp": datetime.now().isoformat(),
        },
        "attendees_raw": attendees,
        "explicit_actions": explicit_actions,
        "decisions_raw": decisions,
        "dates_found": dates,
        "tracker_refs": tracker_refs,
        "sections": sections,
        "full_text": content,
    }

    if tracker_data:
        output["existing_tracker"] = tracker_data

    # Save
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Save complete: {output_path}")


if __name__ == "__main__":
    main()
