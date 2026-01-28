#!/usr/bin/env python3
"""
Phase 1-2: Data extraction for Quality Inspection.
Joins measurements with specifications, computes margins, classifies PASS/BORDERLINE/FAIL.
"""

import argparse
import csv
import json
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
# CSV Parsing
# =============================================================================

def read_csv(path: Path) -> list[dict]:
    """Read CSV file into list of dicts."""
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# =============================================================================
# Margin Calculation & Classification
# =============================================================================

def parse_float(val: str) -> float | None:
    """Parse string to float, return None if empty or invalid."""
    if not val or val.strip() == "":
        return None
    try:
        return float(val.strip())
    except ValueError:
        return None


def compute_margin(value: float, spec_min: float | None, spec_max: float | None) -> tuple[float, str]:
    """
    Compute margin percentage and initial classification.

    margin_pct: how close the value is to the nearest spec limit,
                as a percentage of the spec range.
    - Positive: within spec (% of range away from nearest limit)
    - Negative: outside spec (% beyond the limit)

    Returns: (margin_pct, initial_class)
    """
    # Both limits defined
    if spec_min is not None and spec_max is not None:
        spec_range = spec_max - spec_min
        if spec_range == 0:
            if value == spec_min:
                return 100.0, "PASS"
            else:
                return -100.0, "FAIL"

        if value < spec_min:
            margin_pct = -((spec_min - value) / spec_range * 100)
            return round(margin_pct, 1), "FAIL"
        elif value > spec_max:
            margin_pct = -((value - spec_max) / spec_range * 100)
            return round(margin_pct, 1), "FAIL"
        else:
            dist_to_min = value - spec_min
            dist_to_max = spec_max - value
            margin_pct = min(dist_to_min, dist_to_max) / spec_range * 100
            return round(margin_pct, 1), "PASS"

    # Only max defined
    elif spec_max is not None:
        if value > spec_max:
            if spec_max == 0:
                return -100.0, "FAIL"
            margin_pct = -((value - spec_max) / abs(spec_max) * 100)
            return round(margin_pct, 1), "FAIL"
        else:
            if spec_max == 0:
                return 100.0, "PASS"
            margin_pct = (spec_max - value) / abs(spec_max) * 100
            return round(margin_pct, 1), "PASS"

    # Only min defined
    elif spec_min is not None:
        if value < spec_min:
            if spec_min == 0:
                return -100.0, "FAIL"
            margin_pct = -((spec_min - value) / abs(spec_min) * 100)
            return round(margin_pct, 1), "FAIL"
        else:
            if spec_min == 0:
                return 100.0, "PASS"
            margin_pct = (value - spec_min) / abs(spec_min) * 100
            return round(margin_pct, 1), "PASS"

    # No limits
    return 100.0, "PASS"


def classify_item(margin_pct: float, initial_class: str, borderline_threshold: float) -> str:
    """Refine classification with borderline threshold."""
    if initial_class == "FAIL":
        return "FAIL"
    if margin_pct <= borderline_threshold:
        return "BORDERLINE"
    return "PASS"


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Quality Inspection - Data Extraction (Phase 1-2)"
    )
    parser.add_argument(
        "--measurements",
        required=True,
        help="변환된 측정 데이터 CSV 경로",
    )
    parser.add_argument(
        "--specifications",
        required=True,
        help="변환된 사양 기준 CSV 경로",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="출력 JSON 경로 (raw_data.json)",
    )
    args = parser.parse_args()

    config = load_config()
    borderline_threshold = config.get("judgment", {}).get("borderline_threshold_pct", 10)

    # Read CSV files
    meas_path = Path(args.measurements).resolve()
    spec_path = Path(args.specifications).resolve()

    if not meas_path.exists():
        print(f"[ERROR] File not found: {meas_path}")
        sys.exit(1)
    if not spec_path.exists():
        print(f"[ERROR] File not found: {spec_path}")
        sys.exit(1)

    measurements = read_csv(meas_path)
    specifications = read_csv(spec_path)

    print(f"\n=== Data Extraction ===\n")
    print(f"  Measurements: {len(measurements)} rows")
    print(f"  Specifications: {len(specifications)} rows")
    print(f"  Borderline threshold: {borderline_threshold}%\n")

    # Build spec lookup: (part_id, measurement_type) -> spec row
    spec_lookup = {}
    for spec in specifications:
        key = (spec["part_id"].strip(), spec["measurement_type"].strip())
        spec_lookup[key] = spec

    # Join and compute
    items = []
    parts_summary = {}

    for i, meas in enumerate(measurements):
        part_id = meas["part_id"].strip()
        mtype = meas["measurement_type"].strip()
        value = parse_float(meas["measured_value"])

        if value is None:
            print(f"  [WARN] Invalid value at row {i+1}: {meas}")
            continue

        key = (part_id, mtype)
        spec = spec_lookup.get(key, {})

        part_name = spec.get("part_name", "").strip()
        category = spec.get("category", "").strip()
        spec_min = parse_float(spec.get("spec_min", ""))
        spec_max = parse_float(spec.get("spec_max", ""))
        critical = spec.get("critical", "").strip().lower() == "true"
        unit = meas.get("unit", spec.get("unit", "")).strip()

        margin_pct, raw_class = compute_margin(value, spec_min, spec_max)
        initial_class = classify_item(margin_pct, raw_class, borderline_threshold)

        item = {
            "part_id": part_id,
            "part_name": part_name,
            "category": category,
            "measurement_type": mtype,
            "measured_value": value,
            "unit": unit,
            "spec_min": spec_min,
            "spec_max": spec_max,
            "critical": critical,
            "margin_pct": margin_pct,
            "initial_class": initial_class,
            "inspector": meas.get("inspector", "").strip(),
            "date": meas.get("date", "").strip(),
        }
        items.append(item)

        # Summary per part
        if part_id not in parts_summary:
            parts_summary[part_id] = {
                "part_name": part_name,
                "category": category,
                "measurement_count": 0,
                "all_items_indices": [],
            }
        parts_summary[part_id]["measurement_count"] += 1
        parts_summary[part_id]["all_items_indices"].append(len(items) - 1)

        status_icon = {"PASS": "✅", "BORDERLINE": "⚠️", "FAIL": "❌"}
        print(f"  {status_icon.get(initial_class, '?')} {part_id}/{mtype}: "
              f"{value}{unit} (spec: {spec_min}~{spec_max}, margin: {margin_pct}%) "
              f"→ {initial_class}" + (" [CRITICAL]" if critical else ""))

    # Count summary
    pass_count = sum(1 for it in items if it["initial_class"] == "PASS")
    border_count = sum(1 for it in items if it["initial_class"] == "BORDERLINE")
    fail_count = sum(1 for it in items if it["initial_class"] == "FAIL")

    print(f"\n  Summary: {len(items)} measurements")
    print(f"    PASS: {pass_count} | BORDERLINE: {border_count} | FAIL: {fail_count}")

    # Build output
    output = {
        "meta": {
            "measurements_file": str(meas_path),
            "specifications_file": str(spec_path),
            "extraction_timestamp": datetime.now().isoformat(),
        },
        "items": items,
        "parts_summary": parts_summary,
    }

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Save complete: {output_path}")


if __name__ == "__main__":
    main()
